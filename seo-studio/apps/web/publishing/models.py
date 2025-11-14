# publishing/models.py
from django.conf import settings
from django.db import models
from common.models import BaseModel
from content.models import Post, Media
from core.models import Site

class PublishDestination(BaseModel):
    class DestinationType(models.TextChoices):
        HEADLESS_PUSH = 'headless_push', 'Headless Push'
        STATIC_EXPORT = 'static_export', 'Static Export'
        LOCAL = 'local', 'Local'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='publish_destinations')
    type = models.CharField(max_length=20, choices=DestinationType.choices)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    # Configuration specific to each type
    config = models.JSONField(default=dict, help_text="Type-specific configuration, e.g., endpoint URL, auth headers, target paths.")

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"

class PublishJob(BaseModel):
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        UNPUBLISH = 'unpublish', 'Unpublish'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELED = 'canceled', 'Canceled'

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='publish_jobs')
    destination = models.ForeignKey(PublishDestination, on_delete=models.CASCADE, related_name='jobs')
    action = models.CharField(max_length=10, choices=Action.choices)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    scheduled_at = models.DateTimeField(db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    attempts = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    response_snapshot = models.JSONField(null=True, blank=True, help_text="Snapshot of the response from the destination.")
    idempotency_key = models.CharField(max_length=255, unique=True, help_text="Prevents duplicate jobs for the same content version.")

    def __str__(self) -> str:
        return f"{self.action} job for '{self.post.title}' to '{self.destination.name}'"

class PublishMap(BaseModel):
    """Maps a post to its published state on a specific destination."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='publish_maps')
    destination = models.ForeignKey(PublishDestination, on_delete=models.CASCADE, related_name='maps')

    remote_id_or_path = models.CharField(max_length=1024, help_text="ID for headless, file path for static.")
    remote_url = models.URLField(max_length=1024, blank=True)
    last_sync_at = models.DateTimeField()

    class Meta:
        unique_together = ('post', 'destination')

class MediaSyncMap(BaseModel):
    """Maps a media file to its synced state on a static destination."""
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='media_sync_maps')
    destination = models.ForeignKey(PublishDestination, on_delete=models.CASCADE, related_name='media_maps')

    remote_path = models.CharField(max_length=1024)
    remote_url = models.URLField(max_length=1024, blank=True)
    last_sync_at = models.DateTimeField()

    class Meta:
        unique_together = ('media', 'destination')

class PublishAudit(BaseModel):
    """Logs all publishing actions for auditing purposes."""
    job = models.ForeignKey(PublishJob, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    payload = models.JSONField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Audit: {self.action} by {self.user} at {self.created_at}"

class ContentRenderCache(BaseModel):
    """Stores the pre-rendered output for posts for the 'local' publisher."""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='render_cache')
    rendered_html = models.TextField()
    rendered_meta = models.JSONField()
    rendered_jsonld = models.JSONField()
    content_version_hash = models.CharField(max_length=64)

    class Meta:
        verbose_name = "Content Render Cache"
