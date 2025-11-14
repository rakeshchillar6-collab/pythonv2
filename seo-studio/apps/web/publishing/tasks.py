# publishing/tasks.py
import logging
import hashlib
from celery import shared_task
from django.utils import timezone

from .models import PublishJob, PublishMap, PublishDestination
from .connectors.headless import publish_to_headless
from .connectors.static_export import export_to_static
from .connectors.local import publish_to_local

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60) # Retry up to 3 times, with a 1-minute delay
def execute_publish_job(self, job_id: str):
    """
    Main orchestrator task for all publishing jobs.
    It routes the job to the correct connector and handles state transitions.
    """
    try:
        job = PublishJob.objects.select_related('post', 'destination').get(id=job_id)
    except PublishJob.DoesNotExist:
        logger.warning(f"PublishJob {job_id} not found. Task cannot proceed.")
        return

    job.status = PublishJob.Status.RUNNING
    job.started_at = timezone.now()
    job.attempts = self.request.retries + 1
    job.save()

    try:
        connector_map = {
            PublishDestination.DestinationType.HEADLESS_PUSH: publish_to_headless,
            PublishDestination.DestinationType.STATIC_EXPORT: export_to_static,
            PublishDestination.DestinationType.LOCAL: publish_to_local,
        }

        connector_func = connector_map.get(job.destination.type)
        if not connector_func:
            raise ValueError(f"No connector found for destination type '{job.destination.type}'")

        result = connector_func(job.id)

        # --- Success State Handling ---
        job.status = PublishJob.Status.COMPLETED
        job.response_snapshot = result

        # Update the PublishMap
        PublishMap.objects.update_or_create(
            post=job.post,
            destination=job.destination,
            defaults={
                "remote_id_or_path": result.get("output_path") or result.get("body", {}).get("id"),
                "remote_url": result.get("body", {}).get("url"),
                "last_sync_at": timezone.now(),
            }
        )

    except Exception as e:
        logger.error(f"Publish job {job.id} failed on attempt {job.attempts}. Error: {e}")
        job.status = PublishJob.Status.FAILED
        job.error_message = str(e)

        try:
            # Retry the task if max_retries is not exceeded
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Publish job {job.id} has failed permanently after {job.attempts} attempts.")

    finally:
        job.finished_at = timezone.now()
        job.save()


def enqueue_publish_job(post_id: str, destination_id: str, action: str, scheduled_at=None):
    """
    Creates and enqueues a new publishing job.
    Ensures idempotency by checking for existing jobs with the same content hash.
    """
    from content.models import Post # Avoid circular import
    post = Post.objects.get(id=post_id)

    # Idempotency key based on content version
    content_hash = hashlib.sha256(str(post.updated_at).encode()).hexdigest()
    idempotency_key = f"{post_id}-{destination_id}-{action}-{content_hash}"

    if PublishJob.objects.filter(idempotency_key=idempotency_key).exists():
        logger.info(f"Duplicate publish job detected. Skipping for key: {idempotency_key}")
        return None

    job = PublishJob.objects.create(
        post_id=post_id,
        destination_id=destination_id,
        action=action,
        scheduled_at=scheduled_at or timezone.now(),
        idempotency_key=idempotency_key
    )

    execute_publish_job.apply_async(args=[str(job.id)], eta=job.scheduled_at)

    return job
