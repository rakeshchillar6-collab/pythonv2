# tests/unit/test_seo_authority.py
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from seo_trends.services.topical_authority_calculator import calculate_topical_authority_for_site
from content.models import Post, Category
from core.models import Site, Organization
from graph.models import TopicNode
from seo_trends.models import RankTimeSeries

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="TA Org")
    return Site.objects.create(organization=org, name="TA Site", domain="https://ta.com")

@pytest.fixture
def categories(site):
    cat_a = Category.objects.create(site=site, name="Tech", slug="tech")
    cat_b = Category.objects.create(site=site, name="Marketing", slug="marketing")
    cat_c = Category.objects.create(site=site, name="Empty", slug="empty")
    return {"tech": cat_a, "marketing": cat_b, "empty": cat_c}

@pytest.fixture
def posts(site, categories):
    today = date.today()
    # Tech posts
    p1 = Post.objects.create(site=site, title="Post T1", slug="post-t1", category=categories['tech'], published_at=today - timedelta(days=10))
    p2 = Post.objects.create(site=site, title="Post T2", slug="post-t2", category=categories['tech'], published_at=today - timedelta(days=20))
    # Marketing posts
    p3 = Post.objects.create(site=site, title="Post M1", slug="post-m1", category=categories['marketing'], published_at=today - timedelta(days=100))

    # Create corresponding graph nodes with pagerank
    TopicNode.objects.create(post=p1, pagerank_score=0.5)
    TopicNode.objects.create(post=p2, pagerank_score=0.3)
    TopicNode.objects.create(post=p3, pagerank_score=0.8)

    # Create corresponding time series data
    RankTimeSeries.objects.create(post=p1, date=today, clicks=100, impressions=1000)
    RankTimeSeries.objects.create(post=p2, date=today, clicks=50, impressions=500)
    RankTimeSeries.objects.create(post=p3, date=today, clicks=200, impressions=5000)

    return [p1, p2, p3]

def test_calculate_topical_authority(site, categories, posts):
    # Mock the GSC Property
    mock_gsc_prop = MagicMock()
    mock_gsc_prop.is_active = True

    with pytest.patches('integrations.models.GSCProperty.objects.filter') as mock_filter:
        mock_filter.return_value.first.return_value = mock_gsc_prop

        ta_scores = calculate_topical_authority_for_site(site.id)

    assert len(ta_scores) == 3 # Should include all categories, even empty one

    tech_score_data = next(item for item in ta_scores if item['category_name'] == 'Tech')
    marketing_score_data = next(item for item in ta_scores if item['category_name'] == 'Marketing')
    empty_score_data = next(item for item in ta_scores if item['category_name'] == 'Empty')

    # --- Verify Tech Score ---
    # GSC Metrics: total_clicks = 150, total_impressions = 1500
    # Content Metrics: post_count = 2, avg_pagerank = (0.5+0.3)/2=0.4, avg_freshness_score = ((365-10)/365 + (365-20)/365)/2 = ~0.958
    assert tech_score_data['total_clicks'] == 150
    assert tech_score_data['total_impressions'] == 1500
    assert tech_score_data['post_count'] == 2
    assert pytest.approx(tech_score_data['avg_internal_link_equity'], 0.01) == 0.4
    assert pytest.approx(tech_score_data['avg_freshness_score'], 0.01) == 0.958
    assert tech_score_data['final_score'] > 0

    # --- Verify Marketing Score ---
    # GSC Metrics: total_clicks = 200, total_impressions = 5000
    # Content Metrics: post_count = 1, avg_pagerank = 0.8, avg_freshness_score = (365-100)/365 = ~0.726
    assert marketing_score_data['total_clicks'] == 200
    assert marketing_score_data['post_count'] == 1
    assert pytest.approx(marketing_score_data['avg_internal_link_equity'], 0.01) == 0.8
    assert pytest.approx(marketing_score_data['avg_freshness_score'], 0.01) == 0.726

    # --- Verify Empty Category Score ---
    assert empty_score_data['total_clicks'] == 0
    assert empty_score_data['post_count'] == 0
    assert empty_score_data['avg_internal_link_equity'] == 0
    assert empty_score_data['avg_freshness_score'] == 0
    assert empty_score_data['final_score'] == 0

    # --- Final Check ---
    # Marketing should have a higher score than Tech due to much higher clicks and pagerank, despite being older.
    assert marketing_score_data['final_score'] > tech_score_data['final_score']


def test_calculate_ta_no_gsc(site, categories):
    # Mock the GSC Property to be inactive
    mock_gsc_prop = None
    with pytest.patches('integrations.models.GSCProperty.objects.filter') as mock_filter:
        mock_filter.return_value.first.return_value = mock_gsc_prop

        ta_scores = calculate_topical_authority_for_site(site.id)

    # Should still run, but GSC metrics will be 0
    tech_score_data = next(item for item in ta_scores if item['category_name'] == 'Tech')
    assert tech_score_data['total_clicks'] == 0
    assert tech_score_data['total_impressions'] == 0
    # The final score will be lower, but not zero because other metrics exist
    assert tech_score_data['final_score'] > 0

def test_calculate_ta_no_posts(site):
    Category.objects.create(site=site, name="Tech", slug="tech")
    ta_scores = calculate_topical_authority_for_site(site.id)

    assert len(ta_scores) == 1
    score_data = ta_scores[0]
    assert score_data['post_count'] == 0
    assert score_data['final_score'] == 0
