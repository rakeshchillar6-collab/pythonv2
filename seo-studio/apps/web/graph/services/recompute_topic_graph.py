# graph/services/recompute_topic_graph.py
import re
from typing import List, Tuple
from bs4 import BeautifulSoup
from django.db import transaction, models
from content.models import Post
from ..models import TopicNode, TopicEdge
from .pagerank import calculate_pagerank

def extract_internal_links(post: Post) -> List[Tuple[str, str]]:
    """
    Parses the HTML body of a post and extracts internal links.
    Returns a list of tuples (target_slug, anchor_text).
    """
    links = []
    soup = BeautifulSoup(post.body_html, 'html.parser')

    # This assumes internal links are relative URLs like "/<slug>/"
    # A more robust regex might be needed for different URL structures.
    for a_tag in soup.find_all('a', href=re.compile(r'^/([\w-]+)/$')):
        target_slug = a_tag['href'].strip('/')
        anchor_text = a_tag.get_text(strip=True)
        if target_slug:
            links.append((target_slug, anchor_text))

    return links

@transaction.atomic
def build_graph_from_posts(site_id: str):
    """
    Builds or rebuilds the entire topic graph (Nodes and Edges) for a site
    by scanning all published posts for internal links.
    """
    # 1. Clear existing graph for the site (simple approach)
    TopicNode.objects.filter(post__site_id=site_id).delete()
    # TopicEdge will be deleted by cascade

    # 2. Create TopicNodes for all published posts
    posts = Post.objects.filter(site_id=site_id, status=Post.PostStatus.PUBLISHED)
    nodes_to_create = []
    post_to_node_map = {}
    for post in posts:
        # Assuming a simple logic for role, this should be more sophisticated
        role = TopicNode.NodeRole.SUPPORTING
        if 'pillar' in post.slug: role = TopicNode.NodeRole.PILLAR

        node = TopicNode(post=post, role=role)
        nodes_to_create.append(node)

    TopicNode.objects.bulk_create(nodes_to_create)

    # Re-fetch nodes to build a map from post_id to node_id
    node_map = {str(node.post_id): node for node in TopicNode.objects.filter(post__site_id=site_id)}
    slug_to_post_id_map = {post.slug: str(post.id) for post in posts}

    # 3. Create TopicEdges by extracting links
    edges_to_create = []
    for post in posts:
        source_node = node_map.get(str(post.id))
        if not source_node: continue

        internal_links = extract_internal_links(post)
        for target_slug, anchor in internal_links:
            target_post_id = slug_to_post_id_map.get(target_slug)
            if target_post_id:
                destination_node = node_map.get(target_post_id)
                if destination_node and source_node.id != destination_node.id:
                    edges_to_create.append(
                        TopicEdge(source=source_node, destination=destination_node, anchor_text=anchor)
                    )

    TopicEdge.objects.bulk_create(edges_to_create, ignore_conflicts=True)

    # 4. Update inlinks/outlinks counts on each node
    nodes_to_update = []
    for node in TopicNode.objects.filter(post__site_id=site_id):
        node.inlinks_count = node.incoming_edges.count()
        node.outlinks_count = node.outgoing_edges.count()
        nodes_to_update.append(node)

    TopicNode.objects.bulk_update(nodes_to_update, ['inlinks_count', 'outlinks_count'])

    # 5. Call the PageRank calculation algorithm
    calculate_pagerank(site_id)
