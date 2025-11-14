# reports/tasks.py
import logging
from celery import shared_task
from .services.report_runner import run_report

logger = logging.getLogger(__name__)

@shared_task
def run_report_task(run_id: str):
    """
    Celery task to execute a report run.
    """
    logger.info(f"Starting report run for ID: {run_id}")
    try:
        run_report(run_id)
        logger.info(f"Successfully completed report run for ID: {run_id}")
    except Exception as e:
        logger.error(f"Report run failed for ID {run_id}: {e}")
        # The service itself handles marking the run as failed.
        raise
