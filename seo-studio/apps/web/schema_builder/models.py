# schema_builder/models.py
from django.db import models
from common.models import BaseModel
from core.models import Site
from content.models import Post, Category

class SchemaTemplate(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='schema_templates')
    name = models.CharField(max_length=255)
    schema_type = models.CharField(max_length=100, help_text="e.g., Article, BreadcrumbList, FAQPage")
    template = models.JSONField(help_text="Jinja2 template for the JSON-LD schema.")

    def __str__(self) -> str:
        return f"{self.name} ({self.schema_type})"

class SchemaAssignment(BaseModel):
    class TargetType(models.TextChoices):
        POST_TYPE = 'post_type', 'Post Type'
        CATEGORY = 'category', 'Category'
        GLOBAL = 'global', 'Global'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='schema_assignments')
    template = models.ForeignKey(SchemaTemplate, on_delete=models.CASCADE, related_name='assignments')
    target_type = models.CharField(max_length=20, choices=TargetType.choices)

    # Specific target (optional)
    post_type = models.CharField(max_length=50, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)

    priority = models.PositiveIntegerField(default=10, help_text="Lower number means higher priority.")

    class Meta:
        ordering = ['priority']

    def __str__(self) -> str:
        return f"'{self.template.name}' assigned to {self.get_target_type_display()}"

class SchemaValidationLog(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='schema_validation_logs')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='schema_validation_logs')
    template = models.ForeignKey(SchemaTemplate, on_delete=models.CASCADE)
    is_valid = models.BooleanField()
    errors = models.JSONField(null=True, blank=True)
    rendered_jsonld = models.JSONField()

class SchemaRenderCache(BaseModel):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='schema_cache')
    rendered_jsonld = models.JSONField()
    content_version_hash = models.CharField(max_length=64)
    template_version_hash = models.CharField(max_length=64)
