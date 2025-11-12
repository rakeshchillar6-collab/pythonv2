# vectorsearch/services/chunking.py
import re
from typing import List, TypedDict, Iterator
from django.conf import settings

class ChunkSpec(TypedDict):
    """A dictionary representing the data for a single text chunk."""
    text: str
    ordinal: int
    meta: dict

def normalize_persian_text(text: str) -> str:
    """
    Normalizes Persian text by correcting common character variations and spacing.
    """
    text = text.replace('ي', 'ی').replace('ك', 'ک')
    # Add more normalization rules as needed (e.g., half-space handling)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_by_paragraph(
    text: str,
    max_chunk_length: int,
    chunk_overlap: int
) -> Iterator[str]:
    """
    A simple text splitter that splits by paragraphs and tries to respect max_chunk_length.
    A more advanced implementation would use recursive splitting or semantic chunking.
    """
    paragraphs = text.split('\n')
    buffer = ""

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        if len(buffer) + len(p) + 1 < max_chunk_length:
            buffer += p + "\n"
        else:
            if buffer:
                yield buffer.strip()
            buffer = p + "\n"

    if buffer:
        yield buffer.strip()

def create_chunks(raw_text: str) -> List[ChunkSpec]:
    """
    Splits raw text into manageable chunks for embedding.

    This pipeline performs:
    1. Normalization (especially for Persian text).
    2. Splitting into chunks based on paragraphs.
    3. Assigning an ordinal position to each chunk.
    """
    # Get chunking parameters from Django settings or use defaults
    max_chunk_length = getattr(settings, 'CHUNK_MAX_LENGTH', 1200)
    chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 150) # Note: overlap is not used in this simple splitter

    if not raw_text:
        return []

    # 1. Normalize text
    normalized_text = normalize_persian_text(raw_text)

    # 2. Split text into chunks
    text_chunks = list(split_by_paragraph(normalized_text, max_chunk_length, chunk_overlap))

    # 3. Create ChunkSpec objects
    chunk_specs: List[ChunkSpec] = []
    for i, chunk_text in enumerate(text_chunks):
        chunk_specs.append({
            "text": chunk_text,
            "ordinal": i + 1,
            "meta": {}, # Metadata can be enriched here (e.g., headings)
        })

    return chunk_specs
