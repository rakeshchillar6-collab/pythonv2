# tests/unit/test_graph.py
import pytest
import numpy as np
from bs4 import BeautifulSoup
from unittest.mock import patch

from graph.services.graph_builder import build_graph_from_posts
from graph.services.pagerank import calculate_pagerank
from content.models import Post, Category
from core.models import Site, Organization
from graph.models import TopicNode, TopicEdge

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="Graph Org")
    return Site.objects.create(organization=org, name="Graph Site", domain="https://graph.com")

@pytest.fixture
def posts(site):
    p1 = Post.objects.create(site=site, title="Post A", slug="post-a", full_url="https://graph.com/post-a",
        content_html='<p>This links to <a href="https://graph.com/post-b">Post B</a>.</p>')
    p2 = Post.objects.create(site=site, title="Post B", slug="post-b", full_url="https://graph.com/post-b",
        content_html='<p>This links to <a href="https://graph.com/post-c">Post C</a>.</p>')
    p3 = Post.objects.create(site=site, title="Post C", slug="post-c", full_url="https://graph.com/post-c",
        content_html='<p>This links back to <a href="https://graph.com/post-a">Post A</a> and an external site <a href="https://google.com">Google</a>.</p>')
    p4 = Post.objects.create(site=site, title="Post D", slug="post-d", full_url="https://graph.com/post-d",
        content_html='<p>No internal links.</p>')
    return [p1, p2, p3, p4]

def test_build_graph_from_posts_creates_nodes_and_edges(posts, site):
    build_graph_from_posts(site)

    assert TopicNode.objects.count() == 4
    assert TopicEdge.objects.count() == 3

    post_a = Post.objects.get(slug='post-a')
    post_b = Post.objects.get(slug='post-b')
    post_c = Post.objects.get(slug='post-c')

    node_a = TopicNode.objects.get(post=post_a)
    node_b = TopicNode.objects.get(post=post_b)
    node_c = TopicNode.objects.get(post=post_c)

    assert TopicEdge.objects.filter(source=node_a, target=node_b).exists()
    assert TopicEdge.objects.filter(source=node_b, target=node_c).exists()
    assert TopicEdge.objects.filter(source=node_c, target=node_a).exists()

    # Check that external links are ignored
    assert not TopicEdge.objects.filter(source=node_c, target__post__slug='google.com').exists()

def test_build_graph_is_idempotent(posts, site):
    build_graph_from_posts(site)
    assert TopicNode.objects.count() == 4
    assert TopicEdge.objects.count() == 3

    # Rerunning should not create duplicates
    build_graph_from_posts(site)
    assert TopicNode.objects.count() == 4
    assert TopicEdge.objects.count() == 3

def test_pagerank_calculation(posts, site):
    build_graph_from_posts(site)

    # Run PageRank calculation
    pagerank_scores = calculate_pagerank(site)

    assert len(pagerank_scores) == 4

    post_a = Post.objects.get(slug='post-a')
    post_b = Post.objects.get(slug='post-b')
    post_c = Post.objects.get(slug='post-c')
    post_d = Post.objects.get(slug='post-d')

    # In our graph A->B->C->A, and D is isolated.
    # A, B, C should have roughly equal, higher scores.
    # D should have the base score.
    score_a = pagerank_scores[post_a.id]
    score_b = pagerank_scores[post_b.id]
    score_c = pagerank_scores[post_c.id]
    score_d = pagerank_scores[post_d.id]

    assert score_a > score_d
    assert score_b > score_d
    assert score_c > score_d

    # A, B, and C should be very close in rank because of the cycle
    assert np.isclose(score_a, score_b)
    assert np.isclose(score_b, score_c)

    # Check that the scores were saved to the nodes
    node_a = TopicNode.objects.get(post=post_a)
    assert np.isclose(node_a.pagerank_score, score_a)

def test_pagerank_no_nodes(site):
    # Test case where a site has no posts
    pagerank_scores = calculate_pagerank(site)
    assert pagerank_scores == {}

def test_graph_builder_handles_no_links(site):
    Post.objects.create(site=site, title="Post E", slug="post-e", full_url="https://graph.com/post-e",
        content_html='<p>No links here.</p>')

    build_graph_from_posts(site)
    assert TopicNode.objects.count() == 1
    assert TopicEdge.objects.count() == 0
