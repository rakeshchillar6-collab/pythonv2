# content/models.py
from django.db import models
from django.conf import settings
from common.models import BaseModel
from pgvector.django import VectorField

class Category(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Tag(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Post(BaseModel):
    class PostStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(blank=True)
    excerpt = models.TextField(blank=True)

    status = models.CharField(
        max_length=10, choices=PostStatus.choices, default=PostStatus.DRAFT
    )
    published_at = models.DateTimeField(null=True, blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='posts'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts'
    )
    tags = models.ManyToManyField(Tag, blank=True)

    # Example of embedding field for semantic search on posts
    embedding = VectorField(dimensions=1536, null=True, blank=True)

    def __str__(self):
        return self.title

# Stub models
class Media(BaseModel):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='media/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title

class Revision(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='revisions')
    content_json = models.JSONField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Revision for {self.post.title} at {self.created_at}"
