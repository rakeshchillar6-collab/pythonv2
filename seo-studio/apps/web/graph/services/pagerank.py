# graph/services/pagerank.py
import numpy as np
from django.db import transaction
from ..models import TopicNode, TopicEdge

def calculate_pagerank(site_id: str, damping_factor=0.85, max_iterations=50, tol=1e-6):
    """
    Calculates the internal PageRank for all TopicNodes within a site.
    """
    nodes = list(TopicNode.objects.filter(post__site_id=site_id).order_by('id'))
    if not nodes:
        return

    node_ids = [node.id for node in nodes]
    id_to_index = {node_id: i for i, node_id in enumerate(node_ids)}
    n = len(nodes)

    # Create adjacency matrix
    adj_matrix = np.zeros((n, n))
    edges = TopicEdge.objects.filter(source__post__site_id=site_id).values('source_id', 'destination_id')
    for edge in edges:
        source_idx = id_to_index.get(edge['source_id'])
        dest_idx = id_to_index.get(edge['destination_id'])
        if source_idx is not None and dest_idx is not None:
            adj_matrix[source_idx, dest_idx] = 1

    # Normalize the adjacency matrix
    out_degrees = adj_matrix.sum(axis=1)
    # Handle dangling nodes (nodes with no outgoing links)
    # They distribute their PageRank equally among all other nodes.
    dangling_nodes = np.where(out_degrees == 0)[0]
    # To avoid division by zero, set out_degrees of dangling nodes to 1
    out_degrees[dangling_nodes] = 1

    transition_matrix = adj_matrix / out_degrees[:, np.newaxis]

    # PageRank vector initialization
    pagerank = np.full(n, 1/n)

    # Power iteration method
    for _ in range(max_iterations):
        old_pagerank = pagerank.copy()

        # Calculate contribution from dangling nodes
        dangling_sum = np.sum(pagerank[dangling_nodes])

        pagerank = (damping_factor * (transition_matrix.T @ pagerank + dangling_sum / n)) + ((1 - damping_factor) / n)

        # Check for convergence
        if np.linalg.norm(pagerank - old_pagerank) < tol:
            break

    # Normalize final scores to be between 0 and 1
    min_rank, max_rank = pagerank.min(), pagerank.max()
    if max_rank > min_rank:
        normalized_pagerank = (pagerank - min_rank) / (max_rank - min_rank)
    else:
        normalized_pagerank = pagerank # All ranks are the same

    # Update the TopicNode objects in the database
    with transaction.atomic():
        for i, node in enumerate(nodes):
            node.pagerank_internal = normalized_pagerank[i]
        TopicNode.objects.bulk_update(nodes, ['pagerank_internal'])
