# schema_builder/services/renderer.py
import hashlib
import json
from jinja2 import Environment, FileSystemLoader, meta
from typing import List, Dict, Any

from content.models import Post
from ..models import SchemaAssignment, SchemaRenderCache, SchemaTemplate

class SchemaRenderer:
    def __init__(self, post: Post):
        self.post = post
        self.site = post.site
        self._jinja_env = Environment()

    def _get_relevant_assignments(self) -> List[SchemaAssignment]:
        """
        Finds all schema assignments that apply to this post,
        ordered by priority.
        """
        # This logic can be expanded to be more sophisticated
        assignments = SchemaAssignment.objects.filter(
            site=self.site
        ).filter(
            models.Q(target_type='global') |
            models.Q(target_type='post_type', post_type=self.post.type) |
            models.Q(target_type='category', category=self.post.category)
        ).select_related('template').order_by('priority')

        return list(assignments)

    def _get_context(self) -> Dict[str, Any]:
        """
        Constructs the context dictionary available to the Jinja2 templates.
        """
        # This can be expanded to include scraped data, entity data, etc.
        return {
            "post": self.post,
            "site": self.site,
            "category": self.post.category,
            "tags": list(self.post.tags.all()),
            "author": self.post.author,
        }

    def _render_template(self, template_obj: SchemaTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """Renders a single schema template."""
        template_str = json.dumps(template_obj.template)
        template = self._jinja_env.from_string(template_str)
        rendered_str = template.render(context)
        return json.loads(rendered_str)

    def _calculate_hashes(self, templates: List[SchemaTemplate]) -> (str, str):
        """Calculates hashes for content and templates to manage caching."""
        # Hash of the post content
        content_hash = hashlib.sha256(str(self.post.updated_at).encode()).hexdigest()

        # Hash of all relevant templates
        template_ids = "".join(sorted([str(t.id) for t in templates]))
        template_hash = hashlib.sha256(template_ids.encode()).hexdigest()

        return content_hash, template_hash

    def render(self) -> List[Dict[str, Any]]:
        """
        Renders all applicable schemas for the post, using caching where possible.
        """
        assignments = self._get_relevant_assignments()
        if not assignments:
            return []

        templates = [a.template for a in assignments]
        content_hash, template_hash = self._calculate_hashes(templates)

        # Check cache
        try:
            cache = SchemaRenderCache.objects.get(post=self.post)
            if cache.content_version_hash == content_hash and cache.template_version_hash == template_hash:
                return cache.rendered_jsonld
        except SchemaRenderCache.DoesNotExist:
            pass

        # If cache is invalid or doesn't exist, render
        context = self._get_context()
        rendered_schemas = []
        for template in templates:
            try:
                rendered_schemas.append(self._render_template(template, context))
            except Exception as e:
                # In a real app, log this error
                print(f"Error rendering template {template.name}: {e}")
                continue

        # Update cache
        SchemaRenderCache.objects.update_or_create(
            post=self.post,
            defaults={
                'rendered_jsonld': rendered_schemas,
                'content_version_hash': content_hash,
                'template_version_hash': template_hash,
            }
        )

        return rendered_schemas

def render_schema_for_post(post_id: str) -> List[Dict[str, Any]]:
    """Convenience function to render schemas for a given post ID."""
    try:
        post = Post.objects.select_related('site', 'category', 'author').get(id=post_id)
        renderer = SchemaRenderer(post)
        return renderer.render()
    except Post.DoesNotExist:
        return []
