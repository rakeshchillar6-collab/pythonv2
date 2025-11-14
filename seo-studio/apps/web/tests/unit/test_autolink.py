# tests/unit/test_autolink.py
import pytest
from unittest.mock import patch

from core.models import Site, Organization, User
from content.models import Post, PostRevision
from autolink.models import LinkRule, LinkCandidate
from autolink.services.generator import CandidateGenerator
from autolink.tasks import apply_batch_task
from graph.models import TopicNode

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="Test Org")
    return Site.objects.create(organization=org, name="Test Site", domain="test.com")

@pytest.fixture
def posts(site):
    source = Post.objects.create(
        site=site, title="Source Post", content_html="<p>This post talks about the main keyword.</p>", status='published'
    )
    target = Post.objects.create(
        site=site, title="Target Post", main_keyword="main keyword", status='published'
    )
    # Create TopicNodes for graph testing
    TopicNode.objects.create(post=source)
    TopicNode.objects.create(post=target)
    return source, target

@pytest.fixture
def link_rule(site):
    return LinkRule.objects.create(site=site, is_active=True)

def test_candidate_generator_exact_match(link_rule, posts):
    """Tests that the generator finds exact anchor text matches."""
    source, target = posts
    generator = CandidateGenerator(rule=link_rule)
    generator.generate()

    assert LinkCandidate.objects.count() == 1
    candidate = LinkCandidate.objects.first()

    assert candidate.source_post == source
    assert candidate.target_post == target
    assert candidate.anchor_text == "main keyword"

@patch('autolink.tasks.recompute_topic_graph_task.delay')
def test_apply_batch_task_injects_link(mock_recompute, link_rule, posts):
    """Tests that the apply task correctly injects HTML and updates models."""
    source, target = posts

    # Manually create a candidate
    candidate = LinkCandidate.objects.create(
        site=source.site,
        rule=link_rule,
        source_post=source,
        target_post=target,
        anchor_text="main keyword",
        start_idx=25, end_idx=37,
        context_preview="talks about the main keyword.",
        score=0.8
    )

    # Create a batch
    from autolink.models import LinkBatch
    batch = LinkBatch.objects.create(site=source.site, rule=link_rule, total=1)
    # In a real app, the candidate would be linked to the batch
    # For this test, we'll patch the queryset
    with patch('autolink.tasks.LinkCandidate.objects.filter') as mock_filter:
        mock_filter.return_value = [candidate]

        apply_batch_task(batch.id)

    source.refresh_from_db()
    # Simplified check; this relies on the demo-only replace() logic
    assert '<a href' in source.content_html
    assert 'main keyword' in source.content_html

    # Check that a revision was created
    assert PostRevision.objects.filter(post=source).count() > 0

    # Check that the topic edge was created
    from graph.models import TopicEdge
    assert TopicEdge.objects.filter(source=source.topic_node, target=target.topic_node).exists()

    # Check that PageRank re-computation was triggered
    mock_recompute.assert_called_once_with(str(source.site.id))
