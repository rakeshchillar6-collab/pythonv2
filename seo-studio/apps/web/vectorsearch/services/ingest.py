# vectorsearch/services/ingest.py
import hashlib
from typing import Dict, Any
from django.db import transaction

from ..models import Corpus, Document, EmbeddingVersion, Chunk
from .chunking import create_chunks
from ..tasks import embed_chunks_task

def ingest_document(
    corpus_id: str,
    external_id: str,
    title: str,
    raw_text: str,
    metadata: Dict[str, Any]
) -> Document:
    """
    Manages the ingestion pipeline for a single document.

    This process is idempotent. If the document content has not changed
    (based on a hash of the raw text), no new chunks or tasks are created.

    Returns the created or updated Document instance.
    """
    # 1. Calculate the hash of the new content
    new_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()

    # 2. Get the active embedding version
    active_embedding_version = EmbeddingVersion.objects.filter(is_active=True).first()
    if not active_embedding_version:
        raise ValueError("No active EmbeddingVersion found. Please activate one in the admin panel.")

    # 3. Use a transaction to ensure atomicity
    with transaction.atomic():
        corpus = Corpus.objects.get(id=corpus_id)

        # 4. Get or create the document
        document, created = Document.objects.get_or_create(
            corpus=corpus,
            external_id=external_id,
            defaults={
                'title': title,
                'raw_text': raw_text,
                'metadata': metadata,
                'hash': new_hash,
                'version': 1
            }
        )

        # 5. If the document already existed, check if content has changed
        if not created and document.hash == new_hash:
            # Content is unchanged, no further action needed
            return document

        # 6. If content has changed, update the document and deactivate old chunks
        if not created:
            document.title = title
            document.raw_text = raw_text
            document.metadata = metadata
            document.hash = new_hash
            document.version += 1
            document.save()

            # Deactivate old chunks to exclude them from future searches
            document.chunks.update(is_active=False) # Assumes an `is_active` field on Chunk model

        # 7. Create new chunks from the raw text
        chunk_specs = create_chunks(raw_text)
        new_chunks = []
        for spec in chunk_specs:
            new_chunks.append(
                Chunk(
                    document=document,
                    ordinal=spec['ordinal'],
                    text=spec['text'],
                    # Tokens can be calculated here or in the Celery task
                    tokens=len(spec['text'].split()), # Simple approximation
                    embedding_version=active_embedding_version,
                    meta=spec['meta']
                )
            )

        # 8. Bulk create the new chunk records
        created_chunks = Chunk.objects.bulk_create(new_chunks)
        chunk_ids = [str(chunk.id) for chunk in created_chunks]

    # 9. After the transaction, queue the Celery task for embedding
    if chunk_ids:
        embed_chunks_task.delay(chunk_ids, str(active_embedding_version.id))

    return document

# Note: The `is_active` field is not in the original Chunk model spec.
# Let's add it now. It's crucial for versioning.
