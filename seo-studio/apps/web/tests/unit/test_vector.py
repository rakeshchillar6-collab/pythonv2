# tests/unit/test_vector.py
import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Site
from vectorsearch.models import Corpus, Document, Chunk, EmbeddingVersion
from vectorsearch.services import chunking

pytestmark = pytest.mark.django_db

# --- Fixtures ---
@pytest.fixture
def site():
    return Site.objects.create(name="Test Site", domain="test.com")

@pytest.fixture
def corpus(site):
    return Corpus.objects.create(site=site, name="Test Corpus", lang='en')

@pytest.fixture
def active_embedding_version():
    return EmbeddingVersion.objects.create(
        provider='mock', model_name='mock-v1', dim=1536, is_active=True
    )

@pytest.fixture
def search_api_client(api_client: APIClient, create_user, create_role):
    """Client authenticated with a user having 'editor' role."""
    editor_role = create_role(name="Editor", slug="editor")
    user = create_user(email="searchuser@test.com", roles=[editor_role])
    api_client.force_authenticate(user=user)
    return api_client

# --- Unit Tests for Services ---

def test_chunker_persian_normalization():
    """Test Persian text normalization in the chunker."""
    text = "اين يك متن تست است."
    normalized = chunking.normalize_persian_text(text)
    assert normalized == "این یک متن تست است."

def test_chunker_paragraph_splitting():
    """Test the paragraph-based splitting logic."""
    text = "First paragraph.\n\nSecond paragraph, which is longer.\nThird."
    specs = chunking.create_chunks(text)
    assert len(specs) == 3
    assert specs[0]['text'] == "First paragraph."
    assert specs[1]['ordinal'] == 2

# --- Integration Tests for Ingest Pipeline ---

@patch('vectorsearch.tasks.embed_chunks_task.delay')
def test_ingest_pipeline_creates_document_and_chunks(mock_delay, corpus, active_embedding_version):
    """
    Test the full ingest_document service.
    Ensures it creates a Document, deactivates old Chunks on update,
    creates new ones, and calls the Celery task.
    """
    from vectorsearch.services.ingest import ingest_document

    # --- First Ingest ---
    doc_data = {
        "corpus_id": str(corpus.id),
        "external_id": "post-1",
        "title": "My First Post",
        "raw_text": "This is the first version.",
        "metadata": {"url": "/post-1"},
    }
    document = ingest_document(**doc_data)

    assert Document.objects.count() == 1
    assert document.version == 1
    assert Chunk.objects.filter(document=document, is_active=True).count() == 1
    mock_delay.assert_called_once()
    first_chunk_id = str(Chunk.objects.first().id)
    mock_delay.assert_called_with([first_chunk_id], str(active_embedding_version.id))

    # --- Second Ingest (Content Changed) ---
    mock_delay.reset_mock()
    doc_data['raw_text'] = "This is the updated second version."
    updated_document = ingest_document(**doc_data)

    assert Document.objects.count() == 1
    assert updated_document.version == 2
    # Old chunk should be inactive
    assert Chunk.objects.filter(document=document, is_active=False).count() == 1
    # New chunk should be active
    assert Chunk.objects.filter(document=document, is_active=True).count() == 1
    mock_delay.assert_called_once()


# --- API Tests ---

def test_search_api_unauthorized(api_client: APIClient):
    """Test that the search API requires authentication."""
    url = "/api/vector/search/"
    response = api_client.post(url, {"query": "test"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@patch('vectorsearch.services.search.execute_search')
def test_search_api_calls_service(mock_execute_search, search_api_client: APIClient, active_embedding_version):
    """
    Test that the search API endpoint correctly validates data
    and calls the underlying search service.
    """
    mock_execute_search.return_value = [] # Return an empty list of results

    url = "/api/vector/search/"
    data = {"query": "test query", "mode": "hybrid", "top_k": 5}
    response = search_api_client.post(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    mock_execute_search.assert_called_once()

    # Check that the correct arguments were passed to the service
    call_args = mock_execute_search.call_args[1]
    assert call_args['query_text'] == "test query"
    assert call_args['mode'] == "hybrid"
    assert call_args['top_k'] == 5
