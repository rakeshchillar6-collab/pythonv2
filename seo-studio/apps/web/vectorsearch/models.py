# vectorsearch/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from pgvector.django import VectorField, HNSWIndex

from common.models import BaseModel

class EmbeddedContent(BaseModel):
    """
    A model to store embeddings for various other models (generic relation).
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # The actual embedding vector
    embedding = VectorField(dimensions=1536) # Example dimension for OpenAI's text-embedding-ada-002

    source_text = models.TextField(help_text="The text that was embedded")

    class Meta:
        indexes = [
            # Using HNSW index for efficient similarity search
            HNSWIndex(
                name='embedding_hnsw_index',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_l2_ops'],
            )
        ]
        # Ensure one embedding per content object
        unique_together = ('content_type', 'object_id')

    def __str__(self):
        return f"Embedding for {self.content_object}"
