# tests/unit/test_rss.py
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone

from core.models import Site, Organization
from rss.models import FeedSource, FeedItem
from rss.services.parser import FeedParser
from rss.tasks import process_item_task

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="Test Org")
    return Site.objects.create(organization=org, name="Test Site", domain="test.com")

@pytest.fixture
def feed_source(site):
    return FeedSource.objects.create(
        site=site,
        name="Test Feed",
        url="https://test.com/feed.xml",
        content_policy='draft'
    )

@patch('requests.get')
def test_feed_parser_success(mock_get, feed_source):
    """Tests that the parser correctly parses a mock feed and creates items."""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    with open('tests/fixtures/sample_feed.xml', 'rb') as f:
        mock_response.content = f.read()
    mock_get.return_value = mock_response

    parser = FeedParser(feed_source)
    parser.process()

    feed_source.refresh_from_db()
    assert feed_source.last_error == ""
    assert FeedItem.objects.count() == 2

    item1 = FeedItem.objects.get(guid_hash='a2b21a715565536b334a1b02d849487b3a7cde41ad5369c2089b21f985c67e83')
    assert item1.title == "Test Post 1"
    assert item1.status == 'new'

def test_process_item_creates_draft(feed_source):
    """Tests that the 'process_item' task creates a draft post."""
    item = FeedItem.objects.create(
        source=feed_source,
        guid_hash='test-hash',
        title="New Article from Feed",
        content_raw="<p>This is the content.</p>",
        published_at=timezone.now()
    )

    from content.models import Post
    assert Post.objects.count() == 0

    process_item_task(item.id)

    item.refresh_from_db()
    assert item.status == 'processed'
    assert item.post is not None
    assert Post.objects.count() == 1

    created_post = item.post
    assert created_post.title == "New Article from Feed"
    assert created_post.status == Post.PostStatus.DRAFT

def test_guid_hash_idempotency(feed_source):
    """Tests that items with the same GUID are not created twice."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        with open('tests/fixtures/sample_feed.xml', 'rb') as f:
            mock_response.content = f.read()
        mock_get.return_value = mock_response

        # First run
        parser1 = FeedParser(feed_source)
        parser1.process()
        assert FeedItem.objects.count() == 2

        # Second run should not create new items
        parser2 = FeedParser(feed_source)
        parser2.process()
        assert FeedItem.objects.count() == 2
