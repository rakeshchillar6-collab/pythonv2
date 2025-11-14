# reports/models.py
from django.conf import settings
from django.db import models
from common.models import BaseModel
from core.models import Site

class SavedReport(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='saved_reports')
    name = models.CharField(max_length=255)
    query_dsl = models.JSONField()
    schedule_cron = models.CharField(max_length=100, blank=True, null=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=20, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return self.name

class ReportRun(BaseModel):
    class Status(models.TextChoices):
        RUNNING = 'running', 'Running'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    report = models.ForeignKey(SavedReport, on_delete=models.CASCADE, related_name='runs')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices)
    rows = models.PositiveIntegerField(default=0)
    sample_url = models.URLField(blank=True, null=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str: return f"Run of '{self.report.name}' at {self.created_at}"
