# autolink/models.py
from django.conf import settings
from django.db import models
from common.models import BaseModel
from core.models import Site
from content.models import Post

class LinkRule(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='link_rules')
    scope = models.CharField(max_length=50, default='global')
    include = models.JSONField(default=dict, blank=True)
    exclude = models.JSONField(default=dict, blank=True)
    max_links_per_post = models.PositiveIntegerField(default=5)
    min_distance_chars = models.PositiveIntegerField(default=300)
    anchor_strategy = models.CharField(max_length=50, default='exact')
    capitalize_sensitivity = models.BooleanField(default=False)
    allow_multiple_to_same_target = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

class LinkCandidate(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='link_candidates')
    source_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='source_candidates')
    target_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='target_candidates')
    anchor_text = models.CharField(max_length=255)
    start_idx = models.PositiveIntegerField()
    end_idx = models.PositiveIntegerField()
    context_preview = models.TextField()
    score = models.FloatField()
    reason = models.JSONField(default=dict)
    applied_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-score']

class LinkBatch(BaseModel):
    class Status(models.TextChoices):
        PREPARED = 'prepared', 'Prepared'
        APPLYING = 'applying', 'Applying'
        DONE = 'done', 'Done'
        ABORTED = 'aborted', 'Aborted'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='link_batches')
    rule = models.ForeignKey(LinkRule, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    total = models.PositiveIntegerField()
    applied = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PREPARED)
    notes = models.TextField(blank=True)
