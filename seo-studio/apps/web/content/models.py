# content/models.py
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from core.models import SiteProfile

# --- Taxonomy Models ---
class Category(BaseModel):
    site = models.ForeignKey(SiteProfile, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('site', 'slug')
    def __str__(self) -> str: return self.name

class Tag(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    def __str__(self) -> str: return self.name

# --- Core Content Model: Post ---
class Post(BaseModel):
    class PostType(models.TextChoices):
        ARTICLE = 'ARTICLE', _('Article')
        PRODUCT = 'PRODUCT', _('Product')
        PAGE = 'PAGE', _('Page')

    class PostStatus(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PUBLISHED = 'PUBLISHED', _('Published')
        ARCHIVED = 'ARCHIVED', _('Archived')

    class RobotsMode(models.TextChoices):
        INDEX_FOLLOW = 'INDEX_FOLLOW', _('Index, Follow')
        NOINDEX_FOLLOW = 'NOINDEX_FOLLOW', _('No Index, Follow')
        INDEX_NOFOLLOW = 'INDEX_NOFOLLOW', _('Index, No Follow')
        NOINDEX_NOFOLLOW = 'NOINDEX_NOFOLLOW', _('No Index, No Follow')

    # Core Fields
    site = models.ForeignKey(SiteProfile, on_delete=models.CASCADE, related_name='posts')
    type = models.CharField(max_length=10, choices=PostType.choices, default=PostType.ARTICLE)
    status = models.CharField(max_length=10, choices=PostStatus.choices, default=PostStatus.DRAFT, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='posts')

    # Content Fields
    title = models.CharField(max_length=512)
    title_en = models.CharField(max_length=512, blank=True, help_text="English title, used for generating a clean slug.")
    slug = models.SlugField(max_length=512, allow_unicode=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True, help_text="Normalized plain text version of the body for analysis.")
    summary = models.TextField(blank=True)

    # SEO Fields
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)
    main_keyword = models.CharField(max_length=100, blank=True)
    secondary_keywords = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list)
    lsi_keywords = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list, help_text="Latent Semantic Indexing keywords.")
    entities = ArrayField(models.CharField(max_length=100), blank=True, null=True, default=list, help_text="Named entities found in the text.")

    # Taxonomy
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True)

    # Scheduling & Behavior
    event_start = models.DateTimeField(null=True, blank=True)
    event_end = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    weight = models.IntegerField(default=0, help_text="A weight for ordering, e.g., for featured posts.")
    canonical_url = models.URLField(blank=True, null=True)
    robots_mode = models.CharField(max_length=20, choices=RobotsMode.choices, default=RobotsMode.INDEX_FOLLOW)

    # Computed Fields
    read_time_min = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes.")

    # Timestamps
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="If set, the post will be published at this time.")

    class Meta:
        unique_together = ('site', 'slug')

    def __str__(self) -> str:
        return self.title

# --- History and Versioning Models ---
class PostSlugHistory(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='slug_history')
    old_slug = models.SlugField(max_length=512, allow_unicode=True)

    class Meta: verbose_name_plural = "Post Slug History"

class Redirect301(BaseModel):
    class RedirectReason(models.TextChoices):
        SLUG_CHANGE = 'SLUG_CHANGE', _('Slug Change')
        MANUAL = 'MANUAL', _('Manual')

    site = models.ForeignKey(SiteProfile, on_delete=models.CASCADE, related_name='redirects')
    from_path = models.CharField(max_length=2048, db_index=True)
    to_path = models.CharField(max_length=2048)
    reason = models.CharField(max_length=20, choices=RedirectReason.choices, default=RedirectReason.MANUAL)

    class Meta: unique_together = ('site', 'from_path')

class PostRevision(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='revisions')
    rev_no = models.PositiveIntegerField()
    diff_json = models.JSONField(help_text="A diff between this revision and the previous one.")
    body_html_snapshot = models.TextField()
    meta_snapshot = models.JSONField(help_text="Snapshot of metadata like title, SEO fields, etc.")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    note = models.CharField(max_length=255, blank=True, help_text="A short note describing the changes.")

    class Meta: unique_together = ('post', 'rev_no')

# --- Auxiliary & Block Models ---
class CompetitorURL(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='competitors')
    url = models.URLField(max_length=2048)
    word_count = models.PositiveIntegerField(default=0)
    headings_json = models.JSONField(default=dict, help_text="Extracted H1-H6 headings.")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_fetch_at = models.DateTimeField(null=True, blank=True)

class FaqBlock(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='faq_blocks')
    order = models.PositiveIntegerField()
    question = models.CharField(max_length=512)
    answer_html = models.TextField()
    has_schema = models.BooleanField(default=True, help_text="If true, generate FAQPage schema.org markup.")

    class Meta: ordering = ['order']
