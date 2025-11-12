# tests/unit/test_content.py
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from content.models import Category, Post
from core.models import User

pytestmark = pytest.mark.django_db

@pytest.fixture
def content_editor(create_user, create_role):
    """Creates a user with the 'editor' role."""
    editor_role = create_role(name="Editor", slug="editor")
    return create_user(email="contenteditor@test.com", roles=[editor_role])

@pytest.fixture
def another_user(create_user):
    """Creates a regular user without special roles."""
    return create_user(email="anotheruser@test.com")

# --- Category API Tests ---

def test_list_categories(api_client: APIClient, content_editor):
    """Ensure authenticated editors can list categories."""
    api_client.force_authenticate(user=content_editor)
    Category.objects.create(name="Tech", slug="tech")

    url = "/api/categories/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1

def test_create_category(api_client: APIClient, content_editor):
    """Ensure editors can create a category."""
    api_client.force_authenticate(user=content_editor)
    url = "/api/categories/"
    data = {"name": "Health", "slug": "health"}
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert Category.objects.filter(slug="health").exists()

# --- Post API Tests ---

def test_create_post(api_client: APIClient, content_editor):
    """Ensure an editor can create a post."""
    api_client.force_authenticate(user=content_editor)
    url = "/api/posts/"
    data = {"title": "New Post", "slug": "new-post", "content": "Some content."}
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['author'] == content_editor.email
    assert Post.objects.count() == 1

def test_update_own_post(api_client: APIClient, content_editor):
    """Ensure an editor can update their own post."""
    api_client.force_authenticate(user=content_editor)
    post = Post.objects.create(title="Original", slug="original", author=content_editor)

    url = f"/api/posts/{post.slug}/"
    data = {"title": "Updated Title"}
    response = api_client.patch(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == "Updated Title"

def test_cannot_update_others_post(api_client: APIClient, content_editor, another_user):
    """Ensure a user cannot update a post they do not own."""
    # The post is owned by `another_user`
    post = Post.objects.create(title="Secret Post", slug="secret-post", author=another_user)

    # `content_editor` tries to update it
    api_client.force_authenticate(user=content_editor)
    url = f"/api/posts/{post.slug}/"
    data = {"title": "Hacked"}
    response = api_client.patch(url, data)

    # The `IsOwnerOrAdmin` permission should deny this
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_admin_can_update_others_post(api_client: APIClient, create_user, create_role, another_user):
    """Ensure an admin user can update anyone's post."""
    admin_role = create_role(name="Admin", slug="admin")
    admin_user = create_user(email="admin@test.com", roles=[admin_role])

    post = Post.objects.create(title="Another Post", slug="another-post", author=another_user)

    api_client.force_authenticate(user=admin_user)
    url = f"/api/posts/{post.slug}/"
    data = {"title": "Admin Edited"}
    response = api_client.patch(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == "Admin Edited"
