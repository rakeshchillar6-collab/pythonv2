# tests/unit/test_seo_trends.py
import pytest
from datetime import date, timedelta
from django.utils import timezone

from seo_trends.models import RankTimeSeries, Alert, AlertRule
from seo_trends.services.alert_detector import detect_rank_drops
from core.models import Site, Organization
from content.models import Post

pytestmark = pytest.mark.django_db

@pytest.fixture
def organization():
    return Organization.objects.create(name="Test Org")

@pytest.fixture
def site(organization):
    return Site.objects.create(organization=organization, name="Test Site", domain="https://example.com")

@pytest.fixture
def post(site):
    return Post.objects.create(site=site, title="Test Post", slug="test-post", full_url="https://example.com/test-post")

@pytest.fixture
def alert_rule(site):
    return AlertRule.objects.create(
        site=site,
        name="Default Rank Drop",
        alert_type=Alert.AlertType.RANK_DROP,
        is_active=True,
        configuration={
            "period_1_days": 7,
            "period_2_days": 7,
            "threshold_percentage": 20.0
        }
    )

def test_create_rank_time_series(post):
    today = date.today()
    ts_data = RankTimeSeries.objects.create(
        post=post,
        date=today,
        page=post.full_url,
        country="USA",
        clicks=100,
        impressions=2000,
        ctr=0.05,
        position=2.5
    )
    assert ts_data.post == post
    assert ts_data.date == today
    assert ts_data.position == 2.5
    assert str(ts_data) == f"{post.slug} on {today} (USA)"

def test_alert_rule_creation(site):
    rule = AlertRule.objects.create(
        site=site,
        name="High CTR Drop",
        alert_type=Alert.AlertType.CTR_DROP,
        configuration={"threshold": 0.5}
    )
    assert rule.site == site
    assert rule.name == "High CTR Drop"

# --- Test Alert Detector Service ---

def test_detect_rank_drop_no_significant_change(post, alert_rule):
    # Period 2 (last 7 days)
    for i in range(7):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=5.0)
    # Period 1 (previous 7 days)
    for i in range(7, 14):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=5.1)

    new_alerts = detect_rank_drops(alert_rule)
    assert len(new_alerts) == 0

def test_detect_rank_drop_significant_drop(post, alert_rule):
    # Period 2 (last 7 days avg pos = 10.0)
    for i in range(7):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=10.0)
    # Period 1 (previous 7 days avg pos = 5.0)
    for i in range(7, 14):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=5.0)

    # Change is (10 - 5) / 5 = 100%, which is > 20% threshold
    new_alerts = detect_rank_drops(alert_rule)

    assert len(new_alerts) == 1
    alert = new_alerts[0]
    assert alert.alert_type == Alert.AlertType.RANK_DROP
    assert alert.post == post
    assert alert.status == Alert.AlertStatus.OPEN
    assert alert.details["period_1_avg_position"] == 5.0
    assert alert.details["period_2_avg_position"] == 10.0
    assert alert.details["percentage_change"] == 100.0

def test_detect_rank_drop_improvement_is_not_alert(post, alert_rule):
    # Period 2 (last 7 days avg pos = 5.0)
    for i in range(7):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=5.0)
    # Period 1 (previous 7 days avg pos = 10.0)
    for i in range(7, 14):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=10.0)

    # Change is (5 - 10) / 10 = -50%, which is an improvement
    new_alerts = detect_rank_drops(alert_rule)
    assert len(new_alerts) == 0

def test_detect_rank_drop_ignores_existing_open_alert(post, alert_rule):
    # Create the data that would trigger an alert
    for i in range(7):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=10.0)
    for i in range(7, 14):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=5.0)

    # Create an existing open alert for the same post and rule
    Alert.objects.create(
        rule=alert_rule,
        post=post,
        alert_type=Alert.AlertType.RANK_DROP,
        status=Alert.AlertStatus.OPEN,
        details={"message": "Already exists"}
    )

    new_alerts = detect_rank_drops(alert_rule)
    assert len(new_alerts) == 0

def test_detect_rank_drop_no_data_in_period(post, alert_rule):
    # Only data in one period
    for i in range(7):
        RankTimeSeries.objects.create(post=post, date=date.today() - timedelta(days=i), position=10.0)

    new_alerts = detect_rank_drops(alert_rule)
    assert len(new_alerts) == 0
