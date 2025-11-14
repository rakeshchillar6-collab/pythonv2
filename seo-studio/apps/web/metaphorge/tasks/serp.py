# metaphorge/tasks/serp.py
import logging
from celery import shared_task, group
from django.db.models import Q

from ..models import MFProject, MFKeywordRaw, MFKeywordExpanded, MFSerpResult

logger = logging.getLogger(__name__)

# --- Placeholder SERP Service ---
def get_serp_top10(query: str) -> list[dict]:
    """A mock SERP fetching service."""
    return [{"rank": i, "url": f"https://example.com/{query.replace(' ', '-')}-result-{i}", "title": f"Result {i} for {query}"} for i in range(1, 11)]
# -----------------------------

@shared_task
def fetch_serp_task(project_id: str):
    """
    Orchestrates fetching SERP results for all keywords in the project.
    """
    project = MFProject.objects.get(id=project_id)

    # Get all keywords (raw and expanded) that don't have SERP results yet
    existing_phrases = MFSerpResult.objects.filter(project=project).values_list('phrase', flat=True)

    raw_keywords = MFKeywordRaw.objects.filter(project=project).exclude(phrase__in=existing_phrases)
    expanded_keywords = MFKeywordExpanded.objects.filter(project=project).exclude(phrase__in=existing_phrases)

    phrases_to_fetch = [kw.phrase for kw in raw_keywords] + [kw.phrase for kw in expanded_keywords]

    if not phrases_to_fetch:
        logger.info(f"No new SERP results to fetch for project {project_id}.")
        return

    logger.info(f"Fetching SERP for {len(phrases_to_fetch)} phrases in project {project_id}.")

    # Create a group of tasks to run in parallel, respecting QPS limits
    qps_limit = project.config.get('limits', {}).get('qps', 5)

    serp_tasks = group(fetch_and_save_single_serp.s(project_id, phrase) for phrase in phrases_to_fetch)
    # In a real app, you'd use a rate-limited group or other mechanism
    serp_tasks.apply_async()


@shared_task(rate_limit='5/s', max_retries=3, default_retry_delay=10) # Example rate limit
def fetch_and_save_single_serp(self, project_id: str, phrase: str):
    """Fetches and saves the SERP for a single phrase."""
    try:
        top10 = get_serp_top10(phrase)
        MFSerpResult.objects.create(
            project_id=project_id,
            phrase=phrase,
            top10=top10
        )
    except Exception as e:
        logger.error(f"Failed to fetch SERP for '{phrase}' in project {project_id}. Retrying. Error: {e}")
        self.retry(exc=e)
