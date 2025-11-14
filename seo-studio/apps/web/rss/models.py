# rss/models.py
from django.db import models
from common.models import BaseModel
from core.models import Site
from content.models import Post

class FeedSource(BaseModel):
    class Purpose(models.TextChoices):
        MONITOR = 'monitor', 'Monitor'
        INGEST = 'ingest', 'Ingest'
        BOTH = 'both', 'Both'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='feed_sources')
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=1024, unique=True)
    lang = models.CharField(max_length=10, default='auto')
    purpose = models.CharField(max_length=10, choices=Purpose.choices, default=Purpose.MONITOR)
    check_interval_minutes = models.PositiveIntegerField(default=60)
    max_backfill = models.PositiveIntegerField(default=50)
    parser_profile = models.CharField(max_length=50, default='auto')
    content_policy = models.CharField(max_length=20, default='notify')
    mapping = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name

class FeedItem(BaseModel):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        PROCESSED = 'processed', 'Processed'
        SKIPPED = 'skipped', 'Skipped'
        ERROR = 'error', 'Error'

    source = models.ForeignKey(FeedSource, on_delete=models.CASCADE, related_name='items')
    guid_hash = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=512)
    url = models.URLField(max_length=2048)
    published_at = models.DateTimeField()
    author = models.CharField(max_length=255, blank=True)
    summary_raw = models.TextField(blank=True)
    content_raw = models.TextField(blank=True)
    content_clean = models.TextField(blank=True)
    media = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-published_at']

class FeedRunLog(BaseModel):
    source = models.ForeignKey(FeedSource, on_delete=models.CASCADE, related_name='run_logs')
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    fetched = models.PositiveIntegerField(default=0)
    new = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
