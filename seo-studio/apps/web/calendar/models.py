# calendar/models.py
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from content.models import Post
from core.models import Site

class CalendarLabel(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='calendar_labels')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, help_text="Hex color code, e.g., #RRGGBB")

    class Meta:
        unique_together = ('site', 'name')
    def __str__(self) -> str: return self.name

class ContentTask(BaseModel):
    class TaskType(models.TextChoices):
        WRITE = 'WRITE', _('Write')
        REVIEW = 'REVIEW', _('Review')
        UPDATE = 'UPDATE', _('Update')
        PUBLISH = 'PUBLISH', _('Publish')

    class TaskState(models.TextChoices):
        TODO = 'TODO', _('To Do')
        DOING = 'DOING', _('In Progress')
        BLOCKED = 'BLOCKED', _('Blocked')
        DONE = 'DONE', _('Done')
        SCHEDULED = 'SCHEDULED', _('Scheduled')

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=10, choices=TaskType.choices)
    state = models.CharField(max_length=10, choices=TaskState.choices, default=TaskState.TODO)
    priority = models.PositiveSmallIntegerField(default=0)
    start_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    labels = models.ManyToManyField(CalendarLabel, blank=True)

    class Meta:
        ordering = ['priority', 'due_at']
    def __str__(self) -> str: return f"{self.get_type_display()} for {self.post.title if self.post else 'a new post'}"

class FreshnessRule(BaseModel):
    class Policy(models.TextChoices):
        WARN = 'WARN', _('Warn Only')
        AUTO_SCHEDULE = 'AUTO_SCHEDULE', _('Auto-schedule Update Task')

    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name='freshness_rule')
    max_age_days = models.PositiveIntegerField(default=365)
    traffic_floor = models.PositiveIntegerField(default=100, help_text="Minimum monthly traffic to be considered.")
    rank_floor = models.PositiveIntegerField(default=50, help_text="Minimum average rank to be considered.")
    policy = models.CharField(max_length=20, choices=Policy.choices, default=Policy.WARN)

    def __str__(self) -> str: return f"Freshness Rule for {self.site.name}"
