# alerts/tasks.py
import logging
from celery import shared_task
from .services.detect_alerts import run_alert_detection
from core.models import Site

logger = logging.getLogger(__name__)

@shared_task
def detect_all_alerts():
    """
    A wrapper task that triggers alert detection for all active sites.
    """
    active_sites = Site.objects.all() # In a real app, you might add filtering for active sites.
    logger.info(f"Starting alert detection for {len(active_sites)} site(s).")
    for site in active_sites:
        run_alert_detection.delay(str(site.id)) # Run detection for each site in a separate task

@shared_task
def run_alert_detection_for_site(site_id: str):
    """The actual task that runs the detection logic for a single site."""
    logger.info(f"Running alert detection for site: {site_id}")
    run_alert_detection(site_id)
    return f"Alert detection completed for site {site_id}."
