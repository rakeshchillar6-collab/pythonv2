# reports/models.py
from django.conf import settings
from django.db import models
from common.models import BaseModel
from core.models import Site

class SavedReport(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='saved_reports')
    name = models.CharField(max_length=255)
    query_dsl = models.JSONField(help_text="The secure, whitelisted query DSL for the report.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str: return self.name

class ReportRun(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    report = models.ForeignKey(SavedReport, on_delete=models.CASCADE, related_name='runs')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    finished_at = models.DateTimeField(null=True, blank=True)
    rows_count = models.PositiveIntegerField(default=0)
    download_url = models.URLField(blank=True, null=True, help_text="Link to the generated report file (e.g., in S3).")

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str: return f"Run of '{self.report.name}' at {self.created_at}"
