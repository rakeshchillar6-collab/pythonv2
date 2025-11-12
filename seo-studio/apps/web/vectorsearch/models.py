# vectorsearch/models.py
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from pgvector.django import VectorField, HNSWIndex

from common.models import BaseModel
from core.models import SiteProfile

class Corpus(BaseModel):
    """
    A collection of documents that belong to a specific site and share common properties.
    For example, a "Blog Posts" corpus for a specific site.
    """
    class Language(models.TextChoices):
        PERSIAN = 'fa', _('Persian')
        ENGLISH = 'en', _('English')
        # Add other languages as needed

    class ContentType(models.TextChoices):
        ARTICLE = 'article', _('Article')
        PAGE = 'page', _('Page')
        PRODUCT = 'product', _('Product')
        MEDIA = 'media', _('Media')
        OTHER = 'other', _('Other')

    class Source(models.TextChoices):
        MANUAL = 'manual', _('Manual')
        CRAWLER = 'crawler', _('Crawler')
        RSS = 'rss', _('RSS Feed')
        IMPORT = 'import', _('Import')
        API = 'api', _('API')

    site = models.ForeignKey(SiteProfile, on_delete=models.CASCADE, related_name='corpora')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    lang = models.CharField(max_length=5, choices=Language.choices, default=Language.PERSIAN)
    content_type = models.CharField(max_length=10, choices=ContentType.choices, default=ContentType.ARTICLE)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Corpus"
        verbose_name_plural = "Corpora"
        unique_together = ('site', 'name')

    def __str__(self) -> str:
        return f"{self.name} ({self.site.name})"

class EmbeddingVersion(BaseModel):
    """
    Stores metadata about an embedding model, allowing for versioning and re-embedding.
    """
    class Provider(models.TextChoices):
        MOCK = 'mock', _('Mock')
        OPENAI = 'openai', _('OpenAI')
        OLLAMA = 'ollama', _('Ollama')
        HUGGINGFACE = 'hf', _('HuggingFace')

    provider = models.CharField(max_length=10, choices=Provider.choices, default=Provider.MOCK)
    model_name = models.CharField(max_length=255)
    dim = models.PositiveIntegerField(help_text="The dimensions of the embedding vector.")
    instruction = models.CharField(max_length=512, blank=True, null=True, help_text="Optional instruction prefix for the model.")
    normalize = models.BooleanField(default=True, help_text="Whether to normalize the embedding vectors.")
    is_active = models.BooleanField(default=False, help_text="Indicates the currently active version for new embeddings.")

    class Meta:
        verbose_name = "Embedding Version"
        verbose_name_plural = "Embedding Versions"

    def __str__(self) -> str:
        return f"{self.provider}/{self.model_name} (dim={self.dim})"

class Document(BaseModel):
    """
    Represents a single piece of content (e.g., a blog post, a page) within a corpus.
    """
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name='documents')
    external_id = models.CharField(max_length=255, help_text="The ID of the content in its original source (e.g., Post.id).")
    title = models.CharField(max_length=512)
    raw_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Source-specific metadata like URL, tags, category, etc.")
    hash = models.CharField(max_length=64, help_text="SHA256 hash of the raw_text to detect changes.")
    version = models.PositiveIntegerField(default=1, help_text="Version number, incremented on content change.")
    is_active = models.BooleanField(default=True, help_text="Whether this document is active for searching.")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        unique_together = ('corpus', 'external_id')
        indexes = [models.Index(fields=['corpus', 'external_id'])]

    def __str__(self) -> str:
        return self.title

class Chunk(BaseModel):
    """
    A piece of text split from a Document, along with its embedding.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    ordinal = models.PositiveIntegerField(help_text="The order of the chunk within the document.")
    text = models.TextField()
    tokens = models.PositiveIntegerField(default=0, help_text="Number of tokens in the text.")
    embedding = VectorField(null=True, blank=True, help_text="The vector embedding.")
    embedding_version = models.ForeignKey(EmbeddingVersion, on_delete=models.PROTECT, related_name='chunks')
    meta = models.JSONField(default=dict, blank=True, help_text="Chunk-specific metadata like headings.")
    is_active = models.BooleanField(default=True, db_index=True, help_text="Only active chunks are used in searches.")
    # tsvector = SearchVectorField(null=True) # Will be added in a separate migration

    class Meta:
        verbose_name = "Chunk"
        verbose_name_plural = "Chunks"
        unique_together = ('document', 'ordinal')
        indexes = [
            models.Index(fields=['document', 'ordinal']),
            HNSWIndex(name='chunk_embedding_hnsw_index', fields=['embedding'], opclasses=['vector_l2_ops'])
        ]

    def __str__(self) -> str:
        return f"Chunk {self.ordinal} for {self.document.title}"

class QueryLog(BaseModel):
    """
    Logs search queries for analysis and improvement.
    """
    class SearchMode(models.TextChoices):
        VECTOR = 'vector', _('Vector')
        BM25 = 'bm25', _('BM25')
        HYBRID = 'hybrid', _('Hybrid')
        HYBRID_RERANK = 'hybrid_rerank', _('Hybrid with Rerank')

    site = models.ForeignKey(SiteProfile, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    query_text = models.TextField()
    mode = models.CharField(max_length=15, choices=SearchMode.choices)
    filters = models.JSONField(default=dict, blank=True)
    latency_ms = models.PositiveIntegerField(help_text="Query execution time in milliseconds.")
    results_count = models.PositiveIntegerField()
    trace_id = models.UUIDField(null=True, blank=True)

    class Meta:
        verbose_name = "Query Log"
        verbose_name_plural = "Query Logs"

    def __str__(self) -> str:
        return f"Query on '{self.query_text[:30]}...' ({self.mode})"
