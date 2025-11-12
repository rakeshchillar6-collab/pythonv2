# tests/unit/test_vector.py
import pytest
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Role, User

pytestmark = pytest.mark.django_db

@pytest.fixture
def authorized_vector_client(api_client: APIClient, create_user, create_role):
    """Creates a user with 'editor' role and authenticates the client."""
    editor_role = create_role(name="Editor", slug="editor")
    user = create_user(email="vectoruser@test.com", roles=[editor_role])
    api_client.force_authenticate(user=user)
    return api_client

def test_ingest_endpoint_unauthorized(api_client: APIClient):
    """
    Ensure unauthenticated users cannot access the ingest endpoint.
    """
    url = "/api/vector/ingest/"
    response = api_client.post(url, {})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@patch('vectorsearch.tasks.generate_embedding_for_chunk.delay')
def test_ingest_endpoint_triggers_celery_task(mock_delay, authorized_vector_client: APIClient):
    """
    Ensure the ingest endpoint creates a TextChunk and triggers a Celery task
    when no embedding is provided.
    """
    url = "/api/vector/ingest/"
    data = {
        "title": "Test Ingestion",
        "body": "This is the text to be embedded."
    }
    response = authorized_vector_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.data

    # Check that our mock Celery task was called
    mock_delay.assert_called_once()
    chunk_id = mock_delay.call_args[0][0] # Get the first argument passed to delay()
    assert chunk_id == response.data['id']

def test_search_endpoint(authorized_vector_client: APIClient):
    """
    A simple smoke test for the search endpoint.
    """
    from vectorsearch.models import TextChunk

    # Create a sample chunk with a known vector
    sample_vector = [0.1] * 1536
    TextChunk.objects.create(
        title="Test Chunk",
        body="...",
        embedding=sample_vector
    )

    url = "/api/vector/search/"
    data = {
        "vector": sample_vector,
        "top_k": 5
    }
    response = authorized_vector_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'Test Chunk'
