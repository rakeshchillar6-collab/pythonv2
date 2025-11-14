# graph/services/compute_ta_scores.py
from django.db.models import Sum, Avg
from django.conf import settings
from content.models import Category
from seo_trends.models import RankTimeSeries
from ..models import TopicNode

def normalize(value, min_val, max_val):
    """Normalizes a value to a 0-1 scale."""
    if max_val == min_val:
        return 0.0
    return (value - min_val) / (max_val - min_val)

def calculate_ta_for_category(category: Category) -> dict:
    """
    Calculates the Topical Authority score for a single category.
    """
    posts = category.posts.filter(status='PUBLISHED')
    if not posts.exists():
        return {'score': 0, 'components': {}}

    # --- Get weights from settings (or use defaults) ---
    # Example: TA_WEIGHTS = {'impressions': 0.3, 'pagerank': 0.2, ...}
    weights = getattr(settings, 'TA_WEIGHTS', {
        'impressions': 0.3, 'avg_rank': 0.3, 'num_posts': 0.1,
        'pagerank': 0.2, 'freshness': 0.1
    })

    # --- 1. Gather Raw Metrics ---
    # GSC/SEO Metrics (assuming data is synced)
    gsc_metrics = RankTimeSeries.objects.filter(post__in=posts).aggregate(
        total_impressions=Sum('impressions'), # Assuming 'impressions' field exists
        avg_rank=Avg('position')
    )
    total_impressions = gsc_metrics['total_impressions'] or 0
    avg_rank = gsc_metrics['avg_rank'] or 100 # Default to a high rank if no data

    # Internal Metrics
    num_posts = posts.count()
    pagerank_sum = TopicNode.objects.filter(post__in=posts).aggregate(sum_pr=Sum('pagerank_internal'))['sum_pr'] or 0.0

    # Freshness (simplified: average age of last update in days)
    # Lower is better, so we will invert it
    avg_update_age = (timezone.now() - posts.aggregate(avg_date=Avg('updated_at'))['avg_date']).days

    # --- 2. Calculate Component Scores ---
    # For normalization, we need max values across all categories.
    # This is a simplified approach; a real system might cache these max values.
    # Here we just use some arbitrary max values for demonstration.
    max_impressions = 100000
    max_posts = 100
    max_pagerank_sum = 10.0

    # Invert rank and age so higher is better
    avg_rank_inv = 1 / (1 + avg_rank)
    freshness_inv = 1 / (1 + avg_update_age)

    # Normalize each component
    norm_impressions = normalize(total_impressions, 0, max_impressions)
    norm_avg_rank = avg_rank_inv # Already in a decent range, no need to normalize further
    norm_num_posts = normalize(num_posts, 0, max_posts)
    norm_pagerank = normalize(pagerank_sum, 0, max_pagerank_sum)
    norm_freshness = freshness_inv

    # --- 3. Calculate Final Weighted Score ---
    score = (
        (weights['impressions'] * norm_impressions) +
        (weights['avg_rank'] * norm_avg_rank) +
        (weights['num_posts'] * norm_num_posts) +
        (weights['pagerank'] * norm_pagerank) +
        (weights['freshness'] * norm_freshness)
    ) * 100 # Scale to 0-100

    return {
        'score': round(score, 2),
        'components': {
            'impressions': total_impressions,
            'avg_rank': avg_rank,
            'num_posts': num_posts,
            'pagerank_sum': pagerank_sum,
            'freshness_age_days': avg_update_age,
        }
    }
