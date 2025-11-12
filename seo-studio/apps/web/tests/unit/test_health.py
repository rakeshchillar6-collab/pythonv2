# tests/unit/test_health.py
import pytest
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

def test_health_check_endpoint_unauthenticated(api_client: APIClient):
    """
    Ensure the main /api/health/ endpoint is publicly accessible.
    """
    url = "/api/health/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "database" in response.data
    assert "redis" in response.data
    assert "celery_workers" in response.data
    assert response.data["database"]["status"] == "ok"

def test_integrations_health_check_unauthorized(api_client: APIClient):
    """
    Ensure the /api/integrations/health/ endpoint is protected.
    """
    url = "/api/integrations/health/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_integrations_health_check_authorized(authenticated_client: APIClient):
    """
    Ensure an authenticated user can access the integrations health check.
    (Note: Test assumes user has 'editor' or 'admin' role, which the
     authenticated_client fixture does not guarantee by default, but the
     endpoint requires it. For a real scenario, create a user with the role.)
    """
    from core.models import Role, User

    # We need a user with a role for this test
    role = Role.objects.create(name="Editor", slug="editor")
    user = User.objects.get(email='test@example.com')
    user.roles.add(role)

    url = "/api/integrations/health/"
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
