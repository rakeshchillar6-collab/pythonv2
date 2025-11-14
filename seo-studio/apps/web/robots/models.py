# robots/models.py
from django.db import models
from common.models import BaseModel
from core.models import Site
from content.models import Post

class RobotsGlobal(BaseModel):
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name='robots_global')
    content = models.TextField(help_text="The full content of the robots.txt file.")

    def __str__(self) -> str:
        return f"Global robots.txt for {self.site.name}"

class RobotsRule(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='robots_rules')
    user_agent = models.CharField(max_length=100, default='*', help_text="e.g., '*', 'Googlebot'")
    path_regex = models.CharField(max_length=512, help_text="A regex for the URL path to apply this rule to.")
    is_allowed = models.BooleanField(default=True)

    class Meta:
        ordering = ['path_regex']
        verbose_name = "Robots Path Rule"

    def __str__(self) -> str:
        rule_type = "Allow" if self.is_allowed else "Disallow"
        return f"{rule_type}: {self.path_regex} for {self.user_agent} on {self.site.name}"

class MetaRobotsOverride(BaseModel):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='meta_robots_override')
    noindex = models.BooleanField(default=False)
    nofollow = models.BooleanField(default=False)
    noarchive = models.BooleanField(default=False)

    def to_string(self):
        parts = []
        if self.noindex: parts.append('noindex')
        if self.nofollow: parts.append('nofollow')
        if self.noarchive: parts.append('noarchive')
        return ', '.join(parts) if parts else 'index, follow'

    def __str__(self) -> str:
        return f"Meta robots for '{self.post.title}': {self.to_string()}"
