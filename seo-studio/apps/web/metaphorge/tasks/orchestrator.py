# metaphorge/tasks/orchestrator.py
import logging
from celery import shared_task, chain
from ..models import MFProject
from . import combine, expand, serp, cluster # Import other stage tasks

logger = logging.getLogger(__name__)

# Mapping stages to their corresponding Celery tasks
STAGE_TASK_MAP = {
    MFProject.Stage.COMBINE: combine.combine_seeds_task,
    MFProject.Stage.EXPAND: expand.expand_keywords_task,
    MFProject.Stage.SERP: serp.fetch_serp_task,
    MFProject.Stage.CLUSTER: cluster.cluster_phrases_task,
    # ... add other stages here: LSI, PROMPT, etc.
}

@shared_task(bind=True)
def run_metaphorge_project(self, project_id: str):
    """
    Main orchestrator for a Metaphorge project.
    It manages the state machine and chains the next task.
    """
    try:
        project = MFProject.objects.get(id=project_id)
    except MFProject.DoesNotExist:
        logger.error(f"MFProject with ID {project_id} not found. Stopping pipeline.")
        return

    if project.status in [MFProject.Status.PAUSED, MFProject.Status.STOPPED, MFProject.Status.DONE]:
        logger.info(f"Project {project_id} is in state '{project.status}'. Not proceeding.")
        return

    project.status = MFProject.Status.RUNNING
    project.save(update_fields=['status'])

    # Get the task for the current stage
    current_stage = project.stage
    task_func = STAGE_TASK_MAP.get(current_stage)

    if not task_func:
        logger.error(f"No task found for stage '{current_stage}' in project {project_id}. Stopping.")
        project.status = MFProject.Status.STOPPED
        project.save(update_fields=['status'])
        return

    # Chain the next step: after the current task finishes, this orchestrator will be called again.
    workflow = task_func.s(project_id=project_id).on_error(handle_task_failure.s(project_id=project_id))
    workflow.link(advance_stage_task.s(project_id=project_id))
    workflow.apply_async()

@shared_task
def advance_stage_task(project_id: str):
    """Advances the project to the next stage and re-triggers the orchestrator."""
    project = MFProject.objects.get(id=project_id)

    # Logic to determine the next stage
    current_stage_index = list(MFProject.Stage).index(project.stage)
    if current_stage_index + 1 < len(MFProject.Stage):
        next_stage = list(MFProject.Stage)[current_stage_index + 1]
        project.stage = next_stage
        project.save(update_fields=['stage'])
        run_metaphorge_project.delay(project_id=project_id)
    else:
        # Pipeline is complete
        project.status = MFProject.Status.DONE
        project.save(update_fields=['status'])
        logger.info(f"Metaphorge project {project_id} has completed all stages.")

@shared_task
def handle_task_failure(request, exc, traceback, project_id: str):
    """Handles failures in any pipeline stage."""
    project = MFProject.objects.get(id=project_id)
    project.status = MFProject.Status.STOPPED
    project.save(update_fields=['status'])
    logger.error(f"Pipeline for project {project_id} stopped due to an error in stage '{project.stage}': {exc}")

# --- Control Tasks ---
def start_project(project_id: str):
    project = MFProject.objects.get(id=project_id)
    project.status = MFProject.Status.IDLE # Reset to idle to allow start
    project.stage = MFProject.Stage.COMBINE # Start from the first real stage
    project.save()
    run_metaphorge_project.delay(project_id)

def pause_project(project_id: str):
    MFProject.objects.filter(id=project_id).update(status=MFProject.Status.PAUSED)

def resume_project(project_id: str):
    project = MFProject.objects.get(id=project_id)
    project.status = MFProject.Status.IDLE # Reset status to allow restart
    project.save()
    run_metaphorge_project.delay(project_id)

def stop_project(project_id: str):
    MFProject.objects.filter(id=project_id).update(status=MFProject.Status.STOPPED)
