# metaphorge/tasks/expand.py
import logging
from celery import shared_task, group
from ..models import MFProject, MFCombo, MFKeywordRaw, MFKeywordExpanded

logger = logging.getLogger(__name__)

# --- Placeholder Suggestion Service ---
# In a real implementation, this would connect to a real suggestion API
# or use a local implementation.
def get_suggestions(query: str, max_count: int) -> list[str]:
    """A mock suggestion service."""
    return [f"{query} suggestion {i}" for i in range(max_count)]
# ------------------------------------

@shared_task
def expand_keywords_task(project_id: str):
    """
    Orchestrates the keyword expansion process up to the configured depth.
    """
    project = MFProject.objects.get(id=project_id)
    max_depth = project.config.get('depth', 1)

    # Initial expansion (Depth 0) from combos
    combos = MFCombo.objects.filter(project=project)

    # Create a group of tasks to run in parallel
    initial_tasks = group(fetch_and_save_suggestions.s(project_id, combo.id) for combo in combos)
    initial_tasks.apply_async()

    # TODO: Add logic for subsequent depths (1 to N) if required,
    # which would chain tasks based on the completion of the previous depth.

@shared_task
def fetch_and_save_suggestions(project_id: str, combo_id: str):
    """
    Fetches suggestions for a single combo and saves them as Raw Keywords.
    """
    try:
        project = MFProject.objects.get(id=project_id)
        combo = MFCombo.objects.get(id=combo_id)
        max_suggest = project.config.get('max_suggest', 10)

        query = combo.payload.get('query')
        suggestions = get_suggestions(query, max_suggest)

        for phrase in suggestions:
            MFKeywordRaw.objects.get_or_create(
                project=project,
                phrase=phrase,
                defaults={
                    'seed': combo.seed,
                    'combo': combo,
                    'depth': 0
                }
            )
    except (MFProject.DoesNotExist, MFCombo.DoesNotExist):
        logger.warning(f"Could not find project or combo for combo_id {combo_id}")

# NOTE: The multi-depth expansion (depth > 0) is a complex chaining process
# that would require more intricate Celery workflow patterns (e.g., chords, chains)
# to manage dependencies between depths. For this initial implementation,
# we focus on the successful execution of depth 0.
