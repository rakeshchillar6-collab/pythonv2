# content/tasks.py
import logging
from celery import shared_task
from django.utils import timezone
from .models import Post

logger = logging.getLogger(__name__)

@shared_task
def publish_scheduled_posts():
    """
    Finds and publishes posts that have been scheduled for publication.
    This task is intended to be run periodically (e.g., every minute).
    """
    now = timezone.now()
    posts_to_publish = Post.objects.filter(
        status=Post.PostStatus.DRAFT,
        scheduled_at__isnull=False,
        scheduled_at__lte=now
    )

    count = posts_to_publish.count()
    if count > 0:
        posts_to_publish.update(
            status=Post.PostStatus.PUBLISHED,
            published_at=now
        )
        logger.info(f"Successfully published {count} scheduled post(s).")

    return f"Checked for scheduled posts. Published: {count}."
