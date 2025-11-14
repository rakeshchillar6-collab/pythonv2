# metaphorge/tasks/cluster.py
import logging
import networkx as nx
from itertools import combinations
from celery import shared_task

from ..models import MFProject, MFSerpResult, MFCluster, MFKeywordRaw, MFKeywordExpanded

logger = logging.getLogger(__name__)

@shared_task
def cluster_phrases_task(project_id: str):
    """
    Clusters keywords based on SERP overlap.
    """
    try:
        project = MFProject.objects.get(id=project_id)
        threshold = project.config.get('cluster_threshold', 3)

        serp_results = MFSerpResult.objects.filter(project=project)
        if not serp_results:
            logger.warning(f"No SERP results found for project {project_id}. Skipping clustering.")
            return

        logger.info(f"Starting clustering for project {project_id} with threshold K={threshold}.")

        # Create a graph where nodes are phrases
        G = nx.Graph()
        phrases = [result.phrase for result in serp_results]
        G.add_nodes_from(phrases)

        # Create a map of phrase to its top 10 URLs for efficient lookup
        phrase_to_urls = {result.phrase: {item['url'] for item in result.top10} for result in serp_results}

        # Add edges between phrases if their SERP overlap meets the threshold
        for phrase1, phrase2 in combinations(phrases, 2):
            urls1 = phrase_to_urls.get(phrase1, set())
            urls2 = phrase_to_urls.get(phrase2, set())

            if len(urls1.intersection(urls2)) >= threshold:
                G.add_edge(phrase1, phrase2)

        # Find connected components, which represent the clusters
        connected_components = list(nx.connected_components(G))

        # Clear old clusters
        MFCluster.objects.filter(project=project).delete()

        # Save new clusters
        for component in connected_components:
            cluster_phrases = list(component)

            # Determine main key (shortest phrase)
            main_key = min(cluster_phrases, key=len)
            secondaries = [p for p in cluster_phrases if p != main_key]

            MFCluster.objects.create(
                project=project,
                main_key=main_key,
                secondaries=secondaries,
                phrases=cluster_phrases,
                similarity_k=threshold
            )

        logger.info(f"Clustering complete for project {project_id}. Found {len(connected_components)} clusters.")

    except MFProject.DoesNotExist:
        logger.error(f"MFProject with ID {project_id} not found.")
        raise
