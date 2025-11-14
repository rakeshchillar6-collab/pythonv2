# publishing/connectors/headless.py
import requests
import logging
from typing import Dict, Any

from content.models import Post
from ..models import PublishDestination, PublishJob
from schema_builder.services.renderer import render_schema_for_post

logger = logging.getLogger(__name__)

class HeadlessPublisher:
    def __init__(self, job: PublishJob):
        self.job = job
        self.post = job.post
        self.destination = job.destination
        self.config = self.destination.config

    def _build_payload(self) -> Dict[str, Any]:
        """Constructs the JSON payload to be sent to the headless endpoint."""

        # 1. Get rendered schema
        jsonld = render_schema_for_post(self.post.id)

        # 2. Get meta robots
        meta_robots_override = getattr(self.post, 'meta_robots_override', None)
        robots_content = meta_robots_override.to_string() if meta_robots_override else "index, follow"

        # 3. Get media manifest
        media_manifest = [
            {"id": media.id, "path": media.file.url, "alt": media.alt_text}
            for media in self.post.media.all()
        ]

        # 4. Assemble payload
        payload = {
            "id": str(self.post.id),
            "slug": self.post.slug,
            "type": self.post.type,
            "lang": self.post.language,
            "title": self.post.title,
            "seo": {
                "title": self.post.seo_title,
                "description": self.post.seo_description,
                "canonical": self.post.canonical_url,
                "robots": robots_content,
            },
            "html": self.post.content_html, # Assume this is cleaned HTML
            "jsonld": jsonld,
            "meta": {
                "category": self.post.category.name if self.post.category else None,
                "tags": [tag.name for tag in self.post.tags.all()],
            },
            "media": media_manifest,
            "updated_at": self.post.updated_at.isoformat(),
            "publish_state": 'published' if self.job.action in ['create', 'update'] else 'draft',
        }
        return payload

    def _get_headers(self) -> Dict[str, str]:
        """Constructs the request headers, processing the auth template."""
        headers = self.config.get("headers", {})
        auth_template = self.config.get("auth_header_template", "")

        if auth_template and "{token}" in auth_template:
            # In a real app, the token would come from a secure vault or Django settings
            token = self.config.get("api_key", "")
            headers['Authorization'] = auth_template.format(token=token)

        return headers

    def publish(self) -> Dict:
        """Sends the payload to the destination."""
        endpoint_url = self.config.get("endpoint_url")
        if not endpoint_url:
            raise ValueError("Headless destination is missing 'endpoint_url' in config.")

        payload = self._build_payload()
        headers = self._get_headers()

        http_method = 'post' if self.job.action == 'create' else 'put'

        try:
            response = requests.request(
                method=http_method,
                url=endpoint_url,
                json=payload,
                headers=headers,
                timeout=30 # 30-second timeout
            )
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            return {
                "status_code": response.status_code,
                "body": response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Headless push failed for job {self.job.id}: {e}")
            # The exception will be caught by the Celery task for retry logic
            raise

def publish_to_headless(job_id: str):
    """Entry point for the Celery task."""
    try:
        job = PublishJob.objects.select_related('post', 'destination').get(id=job_id)
        publisher = HeadlessPublisher(job)
        return publisher.publish()
    except PublishJob.DoesNotExist:
        logger.error(f"PublishJob with ID {job_id} not found.")
        raise
