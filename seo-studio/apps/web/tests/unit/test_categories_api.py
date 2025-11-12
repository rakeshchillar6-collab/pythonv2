# tests/unit/test_categories_api.py
import pytest
from rest_framework import status
from content.models import Category

pytestmark = pytest.mark.django_db

@pytest.fixture
def create_category(db):
    def make_category(**kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = 'Test Category'
        if 'slug' not in kwargs:
            kwargs['slug'] = 'test-category'
        return Category.objects.create(**kwargs)
    return make_category

def test_list_categories_unauthenticated(api_client):
    """
    Ensure unauthenticated users cannot list categories.
    """
    url = '/api/categories/'
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_list_categories_authenticated(authenticated_client, create_category):
    """
    Ensure authenticated users can list categories.
    """
    create_category(name="Tech", slug="tech")
    create_category(name="Health", slug="health")

    url = '/api/categories/'
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['name'] == 'Tech'

def test_create_category(authenticated_client):
    """
    Ensure authenticated users can create a new category.
    """
    url = '/api/categories/'
    data = {'name': 'New Category', 'slug': 'new-category'}
    response = authenticated_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert Category.objects.count() == 1
    assert Category.objects.get().name == 'New Category'
