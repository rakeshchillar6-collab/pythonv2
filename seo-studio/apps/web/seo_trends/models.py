# seo_trends/models.py
from django.db import models
from common.models import BaseModel
from content.models import Post

class RankTimeSeries(BaseModel):
    class Engine(models.TextChoices):
        GOOGLE = 'GOOGLE', 'Google'
        # Add other engines later if needed

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='rank_timeseries')
    query = models.CharField(max_length=255)
    engine = models.CharField(max_length=10, choices=Engine.choices, default=Engine.GOOGLE)
    country = models.CharField(max_length=2, default='US')
    device = models.CharField(max_length=10, default='desktop')
    date = models.DateField(db_index=True)
    position = models.FloatField()
    clicks = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    ctr = models.FloatField(default=0.0)

    class Meta:
        verbose_name_plural = "Rank Time Series"
        unique_together = ('post', 'query', 'engine', 'country', 'device', 'date')
        ordering = ['-date']

class SerpVolatility(BaseModel):
    class Vertical(models.TextChoices):
        WEB = 'WEB', 'Web'
        # Can add NEWS, IMAGES etc.

    date = models.DateField(unique=True)
    vertical = models.CharField(max_length=10, choices=Vertical.choices, default=Vertical.WEB)
    value = models.FloatField(help_text="A normalized value (e.g., 0-1 or 0-100) indicating SERP volatility.")

    class Meta:
        verbose_name_plural = "SERP Volatilities"
        ordering = ['-date']

class CannibalizationCase(BaseModel):
    class State(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        RESOLVED = 'RESOLVED', 'Resolved'

    query = models.CharField(max_length=255)
    post_a = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='cannibal_cases_a')
    post_b = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='cannibal_cases_b')
    impressions_shared = models.PositiveIntegerField()
    detected_at = models.DateField(auto_now_add=True)
    state = models.CharField(max_length=10, choices=State.choices, default=State.OPEN)

    class Meta:
        verbose_name_plural = "Cannibalization Cases"
        unique_together = ('query', 'post_a', 'post_b')
