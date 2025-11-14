# graph/tasks.py
import logging
from celery import shared_task
from .services.recompute_topic_graph import build_graph_from_posts

logger = logging.getLogger(__name__)

@shared_task
def recompute_topic_graph_task(site_id: str):
    """
    Celery task to rebuild the topic graph and recalculate PageRank for a site.
    """
    logger.info(f"Starting topic graph recomputation for site: {site_id}")
    try:
        build_graph_from_posts(site_id)
        logger.info(f"Successfully recomputed topic graph for site: {site_id}")
        return f"Graph recomputation complete for site {site_id}."
    except Exception as e:
        logger.error(f"Failed to recompute topic graph for site {site_id}: {e}")
        raise

@shared_task
def compute_ta_scores_task(site_id: str):
    """
    Celery task to calculate Topical Authority for all categories in a site.
    """
    from content.models import Category
    from .services.compute_ta_scores import calculate_ta_for_category

    logger.info(f"Starting Topical Authority calculation for site: {site_id}")
    categories = Category.objects.filter(site_id=site_id)

    results = {}
    for category in categories:
        ta_data = calculate_ta_for_category(category)
        results[category.name] = ta_data['score']
        logger.info(f"TA for '{category.name}': {ta_data['score']}")

    # In a real app, you might save these scores to a cache or a model.
    return f"TA calculation complete for site {site_id}. Results: {results}"
