# sitemap/models.py
from django.db import models
from common.models import BaseModel
from core.models import Site

class SitemapRule(BaseModel):
    class ChangeFreq(models.TextChoices):
        ALWAYS = 'always', 'Always'
        HOURLY = 'hourly', 'Hourly'
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'
        NEVER = 'never', 'Never'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='sitemap_rules')
    post_type = models.CharField(max_length=50, help_text="e.g., 'article', 'product'. Use '*' for all.")
    priority = models.FloatField(default=0.5, help_text="Value between 0.0 and 1.0.")
    changefreq = models.CharField(max_length=10, choices=ChangeFreq.choices, default=ChangeFreq.WEEKLY)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Sitemap rule for {self.post_type} on {self.site.name}"

class HreflangMap(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='hreflang_maps')
    source_url = models.URLField(max_length=1024, unique=True)
    alternates = models.JSONField(help_text="e.g., [{'lang': 'en', 'href': 'https://...'}, ...]")

    def __str__(self) -> str:
        return f"Hreflang for {self.source_url}"

class SitemapBuildLog(BaseModel):
    class Status(models.TextChoices):
        STARTED = 'started', 'Started'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='sitemap_build_logs')
    status = models.CharField(max_length=10, choices=Status.choices)
    file_count = models.PositiveIntegerField(default=0)
    url_count = models.PositiveIntegerField(default=0)
    errors = models.TextField(blank=True)

class IndexationState(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='indexation_states')
    url = models.URLField(max_length=1024, unique=True)
    is_indexed = models.BooleanField(default=False)
    last_checked_at = models.DateTimeField()
    gsc_status = models.CharField(max_length=100, blank=True)
