# reports/tasks.py
import logging
from celery import shared_task
from django.utils import timezone
from croniter import croniter

from .models import SavedReport
from .services.runner import run_saved_report

logger = logging.getLogger(__name__)

@shared_task
def run_scheduled_reports():
    """
    Checks for any saved reports that are due to run based on their cron schedule.
    """
    now = timezone.now()
    scheduled_reports = SavedReport.objects.filter(schedule_cron__isnull=False)

    for report in scheduled_reports:
        # Use croniter to check if the job is due
        base_time = report.last_run_at or now - timezone.timedelta(days=1)
        cron = croniter(report.schedule_cron, base_time)

        if cron.get_next(datetime) <= now:
            logger.info(f"Report '{report.name}' is due. Triggering run.")
            run_saved_report_task.delay(report.id)

@shared_task
def run_saved_report_task(report_id: str):
    """The actual task that executes a single report run."""
    run_saved_report(report_id)
