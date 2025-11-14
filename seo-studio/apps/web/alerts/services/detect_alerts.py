# alerts/services/detect_alerts.py
from datetime import date, timedelta
from django.db.models import Avg
from ..models import Alert, AlertRule
from seo_trends.models import RankTimeSeries
from content.models import Post
from core.models import Site

def check_rank_drop(site: Site, rule: AlertRule):
    """
    Checks for significant rank drops for any tracked query on a site.
    """
    window_days = rule.window_days
    percentage_threshold = rule.thresholds.get('percentage_change', 20)

    end_date = date.today()
    start_date = end_date - timedelta(days=window_days)
    comparison_start_date = start_date - timedelta(days=window_days)

    # Get recent average positions for all queries
    recent_avg_ranks = RankTimeSeries.objects.filter(
        post__site=site,
        date__gte=start_date
    ).values('post_id', 'query').annotate(avg_pos=Avg('position'))

    for item in recent_avg_ranks:
        post = Post.objects.filter(id=item['post_id']).first()
        if not post:
            continue

        baseline_avg = RankTimeSeries.objects.filter(
            post_id=item['post_id'],
            query=item['query'],
            date__gte=comparison_start_date,
            date__lt=start_date
        ).aggregate(avg_pos=Avg('position'))['avg_pos']

        if baseline_avg is None or item['avg_pos'] is None:
            continue

        if item['avg_pos'] > baseline_avg * (1 + percentage_threshold / 100):
            Alert.objects.get_or_create(
                site=site,
                type=Alert.AlertType.RANK_DROP,
                object_id=post.id,
                content_type_id=ContentType.objects.get_for_model(Post).id,
                defaults={
                    'severity': Alert.Severity.MEDIUM,
                    'payload': {
                        'query': item['query'],
                        'old_rank': round(baseline_avg, 2),
                        'new_rank': round(item['avg_pos'], 2),
                        'message': f"Rank for '{item['query']}' on post '{post.title}' dropped from ~{round(baseline_avg, 2)} to ~{round(item['avg_pos'], 2)}."
                    }
                }
            )

def run_alert_detection(site_id: str):
    """
    Runs all active alert rules for a given site.
    """
    try:
        site = Site.objects.get(id=site_id)
        rules = AlertRule.objects.filter(site=site, is_active=True)

        for rule in rules:
            if rule.type == Alert.AlertType.RANK_DROP:
                check_rank_drop(site, rule)

    except Site.DoesNotExist:
        print(f"Site with ID {site_id} not found.")
