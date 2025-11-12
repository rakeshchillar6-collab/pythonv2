# vectorsearch/services.py
from typing import List
from django.db.models import F
from pgvector.django import L2Distance
from .models import TextChunk

def similarity_search(
    vector: List[float],
    top_k: int = 10,
    filters: dict | None = None
) -> List[TextChunk]:
    """
    Performs a similarity search on TextChunk objects.

    Args:
        vector: The embedding vector to search against.
        top_k: The number of top results to return.
        filters: An optional dictionary of filters to apply to the queryset.

    Returns:
        A list of TextChunk objects ordered by similarity.
    """
    if filters is None:
        filters = {}

    # Perform the search using the L2 distance operator (<->)
    # The result is ordered by the distance, so closest matches come first.
    results = TextChunk.objects.annotate(
        distance=L2Distance('embedding', vector)
    ).filter(**filters).order_by('distance')[:top_k]

    return list(results)
