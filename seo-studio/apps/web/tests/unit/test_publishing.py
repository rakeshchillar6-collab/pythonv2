# tests/unit/test_publishing.py
import pytest
from unittest.mock import patch, MagicMock
import hashlib
import requests

from core.models import Site, Organization
from content.models import Post
from publishing.models import PublishDestination, PublishJob
from publishing.tasks import execute_publish_job, enqueue_publish_job
from publishing.connectors.headless import HeadlessPublisher

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="Test Org")
    return Site.objects.create(organization=org, name="Test Site", domain="test.com")

@pytest.fixture
def post(site):
    return Post.objects.create(site=site, title="Test Post", slug="test-post", content_html="<p>Content</p>")

@pytest.fixture
def headless_dest(site):
    return PublishDestination.objects.create(
        site=site,
        name="Headless Test",
        type=PublishDestination.DestinationType.HEADLESS_PUSH,
        config={"endpoint_url": "https://fake-endpoint.com/publish"}
    )

def test_enqueue_job_idempotency(post, headless_dest):
    """Tests that duplicate jobs for the same content version are not created."""
    job1 = enqueue_publish_job(post.id, headless_dest.id, 'create')
    assert job1 is not None
    assert PublishJob.objects.count() == 1

    # Try to enqueue the exact same job again
    job2 = enqueue_publish_job(post.id, headless_dest.id, 'create')
    assert job2 is None
    assert PublishJob.objects.count() == 1

    # Update the post, which changes its content hash
    post.title = "Updated Title"
    post.save()

    # Now a new job should be created
    job3 = enqueue_publish_job(post.id, headless_dest.id, 'update')
    assert job3 is not None
    assert PublishJob.objects.count() == 2

@patch('publishing.tasks.publish_to_headless')
def test_execute_publish_job_routes_to_headless(mock_publish_func, post, headless_dest):
    """Tests that the orchestrator calls the correct connector."""
    job = PublishJob.objects.create(
        post=post,
        destination=headless_dest,
        action='create',
        idempotency_key="test-key"
    )

    execute_publish_job(str(job.id))

    mock_publish_func.assert_called_once_with(str(job.id))
    job.refresh_from_db()
    assert job.status == PublishJob.Status.COMPLETED

@patch('requests.request')
def test_headless_publisher_success(mock_request, post, headless_dest):
    """Tests a successful publish action for the headless connector."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "remote-123", "url": "https://remote.com/post"}
    mock_request.return_value = mock_response

    job = PublishJob.objects.create(post=post, destination=headless_dest, action='create', idempotency_key="key")

    publisher = HeadlessPublisher(job)
    result = publisher.publish()

    assert result['status_code'] == 200
    mock_request.assert_called_once()

@patch('requests.request')
def test_headless_publisher_retry(mock_request, post, headless_dest):
    """Tests that the Celery task will retry on HTTP failure."""
    mock_request.side_effect = requests.exceptions.ConnectionError("Test error")

    job = PublishJob.objects.create(post=post, destination=headless_dest, action='create', idempotency_key="key")

    with pytest.raises(requests.exceptions.ConnectionError):
        # We expect the exception to be raised so Celery can catch it and retry
        publisher = HeadlessPublisher(job)
        publisher.publish()

@patch('publishing.connectors.static_export.Path.mkdir')
@patch('builtins.open')
def test_static_exporter_writes_files(mock_open, mock_mkdir, post):
    """Tests that the static exporter attempts to write the correct files."""
    static_dest = PublishDestination.objects.create(
        site=post.site,
        name="Static Test",
        type=PublishDestination.DestinationType.STATIC_EXPORT,
        config={"target_root": "/tmp/test", "layout_template": "post.html"}
    )
    job = PublishJob.objects.create(post=post, destination=static_dest, action='create', idempotency_key="key")

    from publishing.connectors.static_export import StaticExporter
    exporter = StaticExporter(job)
    result = exporter.publish()

    assert "output_path" in result
    assert mock_mkdir.call_count > 0
    # Check that it tries to open index.html, schema.jsonld, and meta.json
    assert any("index.html" in call[0][0] for call in mock_open.call_args_list)
    assert any("schema.jsonld" in call[0][0] for call in mock_open.call_args_list)
    assert any("meta.json" in call[0][0] for call in mock_open.call_args_list)
