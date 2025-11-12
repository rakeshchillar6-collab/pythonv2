# vectorsearch/models.py
from django.db import models
from pgvector.django import VectorField, HNSWIndex
from common.models import BaseModel

class TextChunk(BaseModel):
    """
    Represents a chunk of text and its corresponding vector embedding.
    This model is used for semantic search.
    """
    title = models.CharField(max_length=255, help_text="A descriptive title for the text chunk.")
    body = models.TextField(help_text="The actual text content that is embedded.")
    embedding = VectorField(
        dimensions=1536,  # Example: OpenAI's text-embedding-ada-002
        null=True,
        blank=True,
        help_text="The vector embedding of the text chunk."
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata, e.g., source URL, document ID."
    )

    class Meta:
        verbose_name = "Text Chunk"
        verbose_name_plural = "Text Chunks"
        indexes = [
            # Use HNSW index for efficient approximate nearest neighbor search.
            # It's generally faster and more accurate for high-dimensional data
            # compared to IVFFlat.
            HNSWIndex(
                name='text_chunk_embedding_hnsw_index',
                fields=['embedding'],
                m=16,              # Recommended range: 4-64
                ef_construction=64, # Recommended range: > ef_search
                opclasses=['vector_l2_ops'], # Use L2 distance for similarity
            )
        ]

    def __str__(self) -> str:
        return self.title
