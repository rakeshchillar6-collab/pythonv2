# publishing/connectors/local.py
import hashlib
from typing import Dict, Any

from content.models import Post
from ..models import PublishJob, ContentRenderCache
from schema_builder.services.renderer import render_schema_for_post

class LocalPublisher:
    def __init__(self, job: PublishJob):
        self.job = job
        self.post = job.post

    def _get_content_version_hash(self) -> str:
        """Generates a hash to represent the current version of the post's content."""
        return hashlib.sha256(str(self.post.updated_at).encode()).hexdigest()

    def publish(self) -> Dict[str, Any]:
        """Renders the post and saves it to the ContentRenderCache."""

        # 1. Render necessary components
        rendered_html = self.post.content_html # Assuming it's clean
        rendered_jsonld = render_schema_for_post(self.post.id)
        rendered_meta = {
            "title": self.post.title,
            "seo_title": self.post.seo_title,
            "seo_description": self.post.seo_description,
            "category": self.post.category.name if self.post.category else None,
            "tags": [tag.name for tag in self.post.tags.all()],
        }

        # 2. Update or create the cache entry
        ContentRenderCache.objects.update_or_create(
            post=self.post,
            defaults={
                'rendered_html': rendered_html,
                'rendered_meta': rendered_meta,
                'rendered_jsonld': rendered_jsonld,
                'content_version_hash': self._get_content_version_hash(),
            }
        )

        # 3. Mark the post as "published" if the action is create/update
        if self.job.action in [PublishJob.Action.CREATE, PublishJob.Action.UPDATE]:
            self.post.status = Post.PostStatus.PUBLISHED
            self.post.save(update_fields=['status'])

        return {
            "status": "success",
            "cache_key": f"post:{self.post.id}",
            "message": "Content render cache updated."
        }

def publish_to_local(job_id: str):
    """Entry point for the Celery task."""
    try:
        job = PublishJob.objects.select_related('post').get(id=job_id)
        publisher = LocalPublisher(job)
        return publisher.publish()
    except PublishJob.DoesNotExist:
        raise
