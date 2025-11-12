# vectorsearch/policies.py
from datetime import timedelta
from django.utils import timezone
from .models import Document, EmbeddingVersion

def should_reembed_document(
    document: Document,
    active_version: EmbeddingVersion
) -> bool:
    """
    Determines if a document should be re-embedded based on defined policies.

    Policies:
    1. If any of the document's active chunks were embedded with a different version.
    2. If the document's content hash has changed (this is handled by the ingest pipeline,
       but could be a fallback check here).
    3. (Optional) If the embeddings have a Time-To-Live (TTL) and have expired.
    """
    # Policy 1: Check if the embedding version of active chunks is outdated.
    # We only need to check one chunk, as all active chunks of a document share the same version.
    first_active_chunk = document.chunks.filter(is_active=True).first()

    if not first_active_chunk or not first_active_chunk.embedding:
        # If there are no active chunks or they haven't been embedded yet, re-embed.
        return True

    if first_active_chunk.embedding_version_id != active_version.id:
        return True

    # Policy 2: TTL (Time-To-Live) - Example: re-embed every 30 days
    # ttl_days = 30
    # if first_active_chunk.created_at < timezone.now() - timedelta(days=ttl_days):
    #     return True

    return False
