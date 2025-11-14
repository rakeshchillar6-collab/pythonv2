# autolink/tasks.py
import logging
from celery import shared_task
from django.utils import timezone

from .models import LinkRule, LinkBatch, LinkCandidate
from .services.generator import generate_candidates_for_rule
from content.models import Post, PostRevision
from graph.models import TopicEdge
from graph.tasks import recompute_topic_graph_task

logger = logging.getLogger(__name__)

@shared_task
def prepare_candidates_task(rule_id: str):
    """Generates link candidates based on a specific rule."""
    generate_candidates_for_rule(rule_id)

@shared_task
def apply_batch_task(batch_id: str):
    """Applies an approved batch of link candidates to their source posts."""
    try:
        batch = LinkBatch.objects.get(id=batch_id)
        batch.status = LinkBatch.Status.APPLYING
        batch.save()

        candidates_to_apply = LinkCandidate.objects.filter(batch=batch) # Assumes relation is added

        applied_count = 0
        for candidate in candidates_to_apply:
            try:
                source_post = candidate.source_post

                # Create a new revision before modifying
                PostRevision.objects.create(
                    post=source_post,
                    content=source_post.content_html,
                    reason="Before auto-linking batch"
                )

                # --- Link Injection Logic ---
                # This is a simplified version. A robust implementation needs to handle
                # precise index mapping from text to HTML.
                content = source_post.content_html
                anchor = candidate.anchor_text
                link = f'<a href="{candidate.target_post.get_absolute_url()}">{anchor}</a>'

                # This simple replace is NOT robust and is for demonstration only.
                # A real version would use start_idx/end_idx on a parsed HTML tree.
                new_content = content.replace(anchor, link, 1)

                source_post.content_html = new_content
                source_post.save()

                # Update TopicEdge
                TopicEdge.objects.get_or_create(
                    source=source_post.topic_node,
                    target=candidate.target_post.topic_node
                )

                candidate.applied_at = timezone.now()
                candidate.save()
                applied_count += 1

            except Exception as e:
                logger.error(f"Failed to apply link candidate {candidate.id}: {e}")

        batch.status = LinkBatch.Status.DONE
        batch.applied = applied_count
        batch.save()

        # Trigger a PageRank re-computation for the entire site
        recompute_topic_graph_task.delay(str(batch.site.id))

    except LinkBatch.DoesNotExist:
        logger.error(f"LinkBatch with ID {batch_id} not found.")
