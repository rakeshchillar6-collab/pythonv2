# rss/tasks.py
import logging
from celery import shared_task
from django.utils import timezone

from .models import FeedSource, FeedItem
from .services.parser import check_feed_source
from content.models import Post # Assuming Post model for draft creation

logger = logging.getLogger(__name__)

@shared_task
def schedule_feed_checks():
    """
    Periodically checks for feed sources that are due for a refresh.
    This task is meant to be run by Celery Beat every few minutes.
    """
    now = timezone.now()
    due_sources = FeedSource.objects.filter(
        is_active=True,
        last_checked_at__lte=now - models.F('check_interval_minutes') * timezone.timedelta(minutes=1)
    )
    for source in due_sources:
        check_source_task.delay(source.id)

@shared_task
def check_source_task(source_id: str):
    """The actual task that fetches and parses a single feed source."""
    check_feed_source(source_id)
    # After fetching, trigger processing for new items
    new_items = FeedItem.objects.filter(source_id=source_id, status=FeedItem.Status.NEW)
    for item in new_items:
        process_item_task.delay(item.id)

@shared_task
def process_item_task(item_id: str):
    """
    Processes a single feed item based on its source's content policy.
    """
    try:
        item = FeedItem.objects.get(id=item_id)
        source = item.source

        # In a real implementation, the 'clean_html' logic would be more robust
        item.content_clean = item.content_raw or item.summary_raw

        if source.content_policy == 'draft':
            # Create a draft post
            post, created = Post.objects.get_or_create(
                site=source.site,
                title=item.title,
                defaults={
                    'status': Post.PostStatus.DRAFT,
                    'content': item.content_clean,
                    'slug': item.title.lower().replace(' ', '-')[:50], # simple slug
                }
            )
            item.post = post
            item.reason = f"Draft created: {post.id}"

        elif source.content_policy == 'notify':
            item.reason = "Notification policy: manual action required."
            # In a real app, this would trigger a notification (e.g., email, webhook)

        elif source.content_policy == 'analysis_only':
            item.reason = "Analysis only: item logged."

        item.status = FeedItem.Status.PROCESSED
        item.save()

    except FeedItem.DoesNotExist:
        logger.warning(f"FeedItem with ID {item_id} not found during processing.")
    except Exception as e:
        logger.error(f"Error processing FeedItem {item_id}: {e}")
        FeedItem.objects.filter(id=item_id).update(status=FeedItem.Status.ERROR, reason=str(e))
