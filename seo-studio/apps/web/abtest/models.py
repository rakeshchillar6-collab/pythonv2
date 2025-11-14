# abtest/models.py
from django.contrib.postgres.fields import ArrayField
from django.db import models
from common.models import BaseModel
from core.models import Site

class TemplatePart(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='template_parts')
    name = models.CharField(max_length=100)
    slot = models.CharField(max_length=50, db_index=True, help_text="e.g., 'hero', 'cta', 'sidebar'")
    html = models.TextField(blank=True)
    is_active = models.BooleanField(default=True) # The one currently in production

    class Meta:
        unique_together = ('site', 'name')

    def __str__(self) -> str: return f"{self.name} ({self.slot})"

class ABTest(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='ab_tests')
    slot = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    # variants is an array of foreign keys to TemplatePart
    variants = models.ManyToManyField(TemplatePart)

    traffic_split = models.JSONField(help_text="e.g., {'variant_id_A': 50, 'variant_id_B': 50}")
    audience_rule = models.JSONField(blank=True, null=True, help_text="Rules for audience targeting.")

    started_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)

    min_sample = models.PositiveIntegerField(default=1000)
    significance_level = models.FloatField(default=0.95)

    winner = models.ForeignKey(TemplatePart, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def __str__(self) -> str: return self.name

class ABMetric(BaseModel):
    ab_test = models.ForeignKey(ABTest, on_delete=models.CASCADE, related_name='metrics')
    variant = models.ForeignKey(TemplatePart, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()

    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('ab_test', 'variant', 'date')
        ordering = ['-date']
