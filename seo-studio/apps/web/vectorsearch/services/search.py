# vectorsearch/services/search.py
import time
from typing import List, Dict, Any, TypedDict
from django.db.models import F, FloatField, Case, When, Value
from django.db.models.functions import Coalesce
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline
from pgvector.django import L2Distance

from ..models import Chunk, Corpus, QueryLog
from ..providers.base import EmbeddingProvider
from ..tasks import log_search_query
from core.models import User, SiteProfile

class SearchResult(TypedDict):
    """A dictionary representing a single search result."""
    chunk_id: str
    document_id: str
    document_title: str
    document_metadata: Dict[str, Any]
    score: float
    snippet: str

def execute_search(
    user: User,
    site: SiteProfile,
    query_text: str,
    embedding_provider: EmbeddingProvider,
    mode: str,
    top_k: int,
    alpha: float,
    with_snippet: bool,
    corpus_ids: List[str] | None = None,
    filters: Dict[str, Any] | None = None,
) -> List[SearchResult]:
    """
    Executes a search query combining vector search and full-text search.
    """
    start_time = time.time()

    # 1. Generate query embedding
    query_vector = embedding_provider.embed([query_text])[0]

    # 2. Base queryset with filters
    base_qs = Chunk.objects.filter(is_active=True)
    if corpus_ids:
        base_qs = base_qs.filter(document__corpus__id__in=corpus_ids)

    # Apply metadata filters (simplified for this example)
    if filters:
        if 'lang' in filters:
            base_qs = base_qs.filter(document__corpus__lang=filters['lang'])
        # Add more filter logic here for tags, dates, etc.

    # 3. Perform Vector Search and/or BM25 Search
    if mode == QueryLog.SearchMode.VECTOR:
        results_qs = vector_search(query_vector, base_qs, top_k)
    elif mode == QueryLog.SearchMode.BM25:
        results_qs = bm25_search(query_text, base_qs, top_k)
    else: # Hybrid search
        results_qs = hybrid_search(query_text, query_vector, base_qs, top_k, alpha)

    # 4. Format the results
    final_results = format_results(results_qs, query_text, with_snippet)

    latency_ms = int((time.time() - start_time) * 1000)

    # 5. Log the query asynchronously
    log_search_query.delay(
        user_id=str(user.id) if user.is_authenticated else None,
        site_id=str(site.id) if site else None,
        query_text=query_text,
        mode=mode,
        filters=filters or {},
        latency_ms=latency_ms,
        results_count=len(final_results)
    )

    return final_results

def vector_search(query_vector, base_qs, top_k):
    return base_qs.annotate(
        distance=L2Distance('embedding', query_vector)
    ).order_by('distance')[:top_k]

def bm25_search(query_text, base_qs, top_k):
    # Determine language from queryset if possible, else default
    lang = base_qs.first().document.corpus.lang if base_qs.exists() else 'simple'
    config = 'english' if lang == 'en' else 'simple'

    query = SearchQuery(query_text, config=config, search_type='websearch')
    return base_qs.annotate(
        rank=SearchRank(F('tsvector'), query)
    ).filter(rank__gte=0.01).order_by('-rank')[:top_k]

def hybrid_search(query_text, query_vector, base_qs, top_k, alpha):
    """
    Performs hybrid search using late fusion of BM25 and vector search scores.
    Scores are normalized to a 0-1 range before fusion.
    """
    # For simplicity, we'll fetch more results from each search and merge
    k_multiplier = 5

    # Get ranked lists from both methods
    vector_results = list(vector_search(query_vector, base_qs, top_k * k_multiplier))
    bm25_results = list(bm25_search(query_text, base_qs, top_k * k_multiplier))

    # Normalize scores (min-max normalization)
    # Note: L2 distance is smaller for better matches, so we invert it.
    max_dist = max(r.distance for r in vector_results) if vector_results else 1.0
    for r in vector_results:
        r.normalized_score = 1 - (r.distance / max_dist)

    max_rank = max(r.rank for r in bm25_results) if bm25_results else 1.0
    for r in bm25_results:
        r.normalized_score = r.rank / max_rank

    # Fuse scores
    fused_scores = {}
    for r in vector_results:
        fused_scores[r.id] = (1 - alpha) * r.normalized_score
    for r in bm25_results:
        fused_scores[r.id] = fused_scores.get(r.id, 0) + (alpha * r.normalized_score)

    # Get top_k results by fused score
    top_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]

    # Fetch final chunks and preserve order
    final_chunks = list(Chunk.objects.filter(id__in=top_ids))
    final_chunks.sort(key=lambda c: fused_scores[c.id], reverse=True)

    # Attach the final fused score to each chunk
    for chunk in final_chunks:
        chunk.final_score = fused_scores[chunk.id]

    return final_chunks

def format_results(results_qs, query_text, with_snippet) -> List[SearchResult]:
    """Formats the queryset into a list of dictionaries."""
    formatted = []
    for chunk in results_qs:
        snippet = ""
        if with_snippet:
            if hasattr(chunk, 'rank'): # From BM25
                lang = chunk.document.corpus.lang
                config = 'english' if lang == 'en' else 'simple'
                snippet = SearchHeadline(
                    F('text'), SearchQuery(query_text, config=config),
                    start_sel='<mark>', stop_sel='</mark>',
                ).resolve_expression(chunk).expressions[0]
            else: # Vector search
                snippet = chunk.text[:250] + "..." # Simple truncation

        formatted.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document.id,
            "document_title": chunk.document.title,
            "document_metadata": chunk.document.metadata,
            "score": getattr(chunk, 'final_score', getattr(chunk, 'rank', 1 - getattr(chunk, 'distance', 1))),
            "snippet": snippet,
        })
    return formatted
