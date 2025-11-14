# alerts/models.py
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from common.models import BaseModel
from core.models import Site

class Alert(BaseModel):
    class AlertType(models.TextChoices):
        RANK_DROP = 'RANK_DROP', 'Rank Drop'
        RANK_SPIKE = 'RANK_SPIKE', 'Rank Spike'
        CLICK_DROP = 'CLICK_DROP', 'Click Drop'
        CLICK_SPIKE = 'CLICK_SPIKE', 'Click Spike'
        DEINDEXED = 'DEINDEXED', 'De-indexed'
        CRAWL_DROP = 'CRAWL_DROP', 'Crawl Drop'
        CANNIBALIZATION = 'CANNIBALIZATION', 'Cannibalization'
        STALE_CONTENT = 'STALE_CONTENT', 'Stale Content'
        TREND_OPPORTUNITY = 'TREND_OPPORTUNITY', 'Trend Opportunity'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='alerts')
    type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)

    # Generic relation to the subject of the alert (e.g., a Post, a Query)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    subject = GenericForeignKey('content_type', 'object_id')

    payload = models.JSONField(help_text="Detailed information about the alert.")
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.get_type_display()} ({self.get_severity_display()}) for {self.site.name}"

class AlertRule(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='alert_rules')
    type = models.CharField(max_length=20, choices=Alert.AlertType.choices)
    thresholds = models.JSONField(help_text="Rule-specific thresholds, e.g., {'percentage_change': 20}")
    window_days = models.PositiveIntegerField(default=14, help_text="The time window to compare against.")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('site', 'type')

    def __str__(self) -> str:
        return f"Rule for {self.get_type_display()} on {self.site.name}"
