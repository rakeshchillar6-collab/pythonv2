# publishing/connectors/static_export.py
import json
import os
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from content.models import Post, Media
from ..models import PublishDestination, PublishJob, MediaSyncMap
from schema_builder.services.renderer import render_schema_for_post

class StaticExporter:
    def __init__(self, job: PublishJob):
        self.job = job
        self.post = job.post
        self.destination = job.destination
        self.config = self.destination.config
        self.base_path = Path(self.config.get("target_root", "/tmp/static_exports"))
        self.jinja_env = Environment(loader=FileSystemLoader(self.config.get("template_dir", "templates/")))

    def _get_output_path(self) -> Path:
        """Determines the output directory for the post."""
        # e.g., /YYYY/MM/DD/slug/
        date_path = self.post.published_at.strftime("%Y/%m/%d")
        return self.base_path / date_path / self.post.slug

    def _handle_media(self, output_path: Path):
        """Copies or links media assets based on the asset policy."""
        asset_policy = self.config.get("asset_policy", "link")
        if asset_policy == "copy":
            media_path = output_path / "media"
            media_path.mkdir(parents=True, exist_ok=True)

            for media_item in self.post.media.all():
                source_file = Path(media_item.file.path)
                destination_file = media_path / source_file.name
                shutil.copy(source_file, destination_file)

                # Update map
                MediaSyncMap.objects.update_or_create(
                    media=media_item,
                    destination=self.destination,
                    defaults={
                        "remote_path": str(destination_file),
                        "last_sync_at": self.job.started_at,
                    }
                )

    def _write_files(self, output_path: Path):
        """Renders and writes the HTML and JSON files."""
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Render and write schema.jsonld
        jsonld_data = render_schema_for_post(self.post.id)
        with open(output_path / "schema.jsonld", "w") as f:
            json.dump(jsonld_data, f, indent=2)

        # 2. Render and write meta.json
        meta_data = {
            "id": str(self.post.id),
            "slug": self.post.slug,
            "title": self.post.title,
            # ... add other meta fields as needed
        }
        with open(output_path / "meta.json", "w") as f:
            json.dump(meta_data, f, indent=2)

        # 3. Render and write index.html using Jinja template
        layout_template_name = self.config.get("layout_template", "post.html")
        template = self.jinja_env.get_template(layout_template_name)
        html_content = template.render(post=self.post, meta=meta_data, jsonld=jsonld_data)

        with open(output_path / "index.html", "w") as f:
            f.write(html_content)

    def publish(self) -> Dict:
        """Exports the post to static files."""
        output_path = self._get_output_path()

        self._write_files(output_path)
        self._handle_media(output_path)

        return {
            "status": "success",
            "output_path": str(output_path),
            "files_written": ["index.html", "meta.json", "schema.jsonld"]
        }

def export_to_static(job_id: str):
    """Entry point for the Celery task."""
    try:
        job = PublishJob.objects.select_related('post', 'destination').get(id=job_id)
        exporter = StaticExporter(job)
        return exporter.publish()
    except PublishJob.DoesNotExist:
        raise
