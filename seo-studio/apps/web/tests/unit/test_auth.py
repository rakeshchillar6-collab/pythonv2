# tests/unit/test_auth.py
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from core.models import User, Role

pytestmark = pytest.mark.django_db

@pytest.fixture
def admin_user(create_user, create_role):
    admin_role = create_role(name="Admin", slug="admin")
    return create_user(email="admin@test.com", roles=[admin_role])

@pytest.fixture
def editor_user(create_user, create_role):
    editor_role = create_role(name="Editor", slug="editor")
    return create_user(email="editor@test.com", roles=[editor_role])

def test_login_and_get_token(api_client: APIClient, create_user, test_password):
    """
    Ensure a user can log in and receive JWT tokens.
    """
    user = create_user(email="login@test.com")
    url = "/api/auth/token/"
    response = api_client.post(url, {"email": user.email, "password": test_password})

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data

def test_refresh_token(api_client: APIClient, create_user, test_password):
    """
    Ensure a user can refresh their access token.
    """
    user = create_user(email="refresh@test.com")
    login_url = "/api/auth/token/"
    login_response = api_client.post(login_url, {"email": user.email, "password": test_password})
    refresh_token = login_response.data["refresh"]

    refresh_url = "/api/auth/token/refresh/"
    refresh_response = api_client.post(refresh_url, {"refresh": refresh_token})

    assert refresh_response.status_code == status.HTTP_200_OK
    assert "access" in refresh_response.data

def test_role_permission_unauthorized(api_client: APIClient, editor_user):
    """
    Ensure a user without the 'admin' role gets a 403 Forbidden error
    when trying to access an admin-only endpoint.
    """
    api_client.force_authenticate(user=editor_user)

    # /api/users/ is restricted to admins
    url = "/api/users/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_role_permission_authorized(api_client: APIClient, admin_user):
    """
    Ensure a user with the 'admin' role can access an admin-only endpoint.
    """
    api_client.force_authenticate(user=admin_user)

    url = "/api/users/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK

def test_user_has_role_method(create_user, create_role):
    """
    Test the `has_role` method on the custom User model.
    """
    role1 = create_role(slug="role1")
    role2 = create_role(slug="role2")
    user = create_user(roles=[role1])

    assert user.has_role("role1") is True
    assert user.has_role("role2") is False
    assert user.has_role("role1", "role2") is True
