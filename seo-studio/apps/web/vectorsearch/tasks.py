# vectorsearch/tasks.py
import logging
from typing import List
from celery import shared_task
from django.conf import settings
from django.db import transaction

from .models import Chunk, EmbeddingVersion
from .providers.utils import get_provider_instance

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def embed_chunks_task(self, chunk_ids: List[str], embedding_version_id: str):
    """
    Celery task to generate and save embeddings for a batch of Chunks.
    """
    try:
        embedding_version = EmbeddingVersion.objects.get(id=embedding_version_id)
        provider = get_provider_instance(embedding_version)

        chunks_to_embed = list(Chunk.objects.filter(id__in=chunk_ids, embedding__isnull=True))
        if not chunks_to_embed:
            logger.info("No chunks found to embed for the given IDs.")
            return "No chunks to embed."

        texts_to_embed = [chunk.text for chunk in chunks_to_embed]

        # --- Batching Logic ---
        batch_size = getattr(settings, 'EMBED_BATCH_SIZE', 64)
        total_chunks = len(texts_to_embed)
        logger.info(f"Starting embedding for {total_chunks} chunk(s) with provider {embedding_version.provider} and batch size {batch_size}.")

        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks_to_embed[i:i + batch_size]
            batch_texts = texts_to_embed[i:i + batch_size]

            logger.info(f"Processing batch {i//batch_size + 1}...")

            # Generate embeddings for the current batch
            embeddings = provider.embed(batch_texts)

            # Assign embeddings back to the chunk objects
            for chunk, embedding in zip(batch_chunks, embeddings):
                chunk.embedding = embedding

            # Bulk update the database in a transaction for this batch
            with transaction.atomic():
                Chunk.objects.bulk_update(batch_chunks, ['embedding'])

            logger.info(f"Successfully updated embeddings for batch {i//batch_size + 1}.")

        return f"Successfully embedded {total_chunks} chunks."

    except EmbeddingVersion.DoesNotExist:
        logger.error(f"EmbeddingVersion with ID {embedding_version_id} not found.")
        # No retry, as this is a permanent failure
    except Exception as e:
        logger.error(f"An unexpected error occurred in embed_chunks_task: {e}")
        # Retry the task for transient errors (e.g., provider API down)
        raise self.retry(exc=e)

@shared_task
def reembed_corpus_task(corpus_id: str, target_embedding_version_id: str):
    """
    Stub for a task that re-embeds all documents in a corpus with a new model.
    """
    logger.info(f"Queueing re-embedding for corpus {corpus_id} to version {target_embedding_version_id}...")
    # In a real implementation, this would find all documents in the corpus
    # and trigger `ingest_document` for each, or a more direct re-embedding flow.
    return "Re-embedding task for corpus queued."

@shared_task
def maintain_indexes_task():
    """
    Stub for a task that performs maintenance on vector indexes.
    """
    from django.db import connection
    logger.info("Running vector index maintenance...")
    # Example for IVFFlat (not needed for HNSW, but good practice to have)
    # with connection.cursor() as cursor:
    #     cursor.execute("SET enable_seqscan = off;")
    #     cursor.execute("VACUUM ANALYZE vectorsearch_chunk;")
    return "Index maintenance task finished."

@shared_task
def apply_reembedding_policy():
    """
    Periodically checks all active documents against re-embedding policies
    and queues them for ingestion if needed.
    """
    from .models import Document, EmbeddingVersion
    from .policies import should_reembed_document
    from .services.ingest import ingest_document

    active_version = EmbeddingVersion.objects.filter(is_active=True).first()
    if not active_version:
        logger.warning("Re-embedding policy check skipped: No active EmbeddingVersion found.")
        return "Skipped: No active embedding version."

    logger.info(f"Applying re-embedding policy for active version: {active_version.id}")

    documents_to_reembed = []
    # Iterate in chunks to avoid loading all documents into memory at once
    for doc in Document.objects.filter(is_active=True).iterator(chunk_size=1000):
        if should_reembed_document(doc, active_version):
            documents_to_reembed.append(doc)

    if not documents_to_reembed:
        logger.info("No documents found that require re-embedding.")
        return "No documents to re-embed."

    logger.info(f"Found {len(documents_to_reembed)} document(s) to re-embed. Queueing ingestion tasks...")

    for doc in documents_to_reembed:
        # Re-triggering the ingest pipeline will handle versioning and re-chunking
        ingest_document(
            corpus_id=str(doc.corpus_id),
            external_id=doc.external_id,
            title=doc.title,
            raw_text=doc.raw_text,
            metadata=doc.metadata
        )

    return f"Queued {len(documents_to_reembed)} document(s) for re-embedding."

@shared_task
def log_search_query(
    user_id: str | None,
    site_id: str | None,
    query_text: str,
    mode: str,
    filters: dict,
    latency_ms: int,
    results_count: int
):
    """Asynchronously logs a search query to the database."""
    from .models import QueryLog

    QueryLog.objects.create(
        user_id=user_id,
        site_id=site_id,
        query_text=query_text,
        mode=mode,
        filters=filters,
        latency_ms=latency_ms,
        results_count=results_count,
    )
    logger.info(f"Logged search query: '{query_text[:50]}...'")
