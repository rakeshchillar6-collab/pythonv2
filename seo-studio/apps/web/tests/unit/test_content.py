# tests/unit/test_content.py
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from content.models import Post, Category, Redirect301, PostSlugHistory
from core.models import User, Site

pytestmark = pytest.mark.django_db

# --- Fixtures ---
@pytest.fixture
def site():
    return Site.objects.create(name="Test Site", domain="test.com")

@pytest.fixture
def editor_user(create_user, create_role):
    editor_role = create_role(name="Editor", slug="editor")
    return create_user(email="editor@test.com", roles=[editor_role])

# --- Signal Tests ---
def test_slug_change_creates_redirect_and_history(site, editor_user):
    """
    Ensure that changing a post's slug correctly creates a Redirect301
    and a PostSlugHistory record.
    """
    post = Post.objects.create(
        title="Original Title",
        slug="original-slug",
        site=site,
        author=editor_user
    )

    assert Redirect301.objects.count() == 0
    assert PostSlugHistory.objects.count() == 0

    # Change the slug and save
    post.slug = "new-updated-slug"
    post.save()

    assert Redirect301.objects.count() == 1
    redirect = Redirect301.objects.first()
    assert redirect.from_path == "/original-slug/"
    assert redirect.to_path == "/new-updated-slug/"
    assert redirect.site == site

    assert PostSlugHistory.objects.count() == 1
    history = PostSlugHistory.objects.first()
    assert history.old_slug == "original-slug"
    assert history.post == post

# --- Rank-Me Service Tests (Smoke Test) ---
def test_rank_me_evaluator(site, editor_user):
    """
    A simple smoke test for the Rank-Me evaluator service.
    """
    from rankme import evaluate_post

    post = Post.objects.create(
        title="Test Post for SEO",
        slug="test-post-for-seo",
        site=site,
        author=editor_user,
        main_keyword="seo",
        body_text="This is a test about seo."
    )

    evaluation = evaluate_post(post.pk)

    assert "score" in evaluation
    assert "checks" in evaluation
    assert evaluation['score'] > 0
    # Find the keyword density check and verify it ran
    density_check = next((c for c in evaluation['checks'] if c['id'] == 'keyword_density'), None)
    assert density_check is not None
    assert density_check['is_ok'] is False # Density is too high in this short text

# --- Public API Tests ---
def test_public_post_list_api(api_client: APIClient, site, editor_user):
    """
    Ensure the public API for posts only returns published posts.
    """
    # Create one published and one draft post
    Post.objects.create(
        title="Published Post", slug="published-post", site=site,
        author=editor_user, status=Post.PostStatus.PUBLISHED
    )
    Post.objects.create(
        title="Draft Post", slug="draft-post", site=site,
        author=editor_user, status=Post.PostStatus.DRAFT
    )

    url = "/api/public/posts/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['title'] == "Published Post"

def test_public_post_detail_api(api_client: APIClient, site, editor_user):
    """
    Ensure the public detail endpoint returns correct data and 404 for drafts.
    """
    published_post = Post.objects.create(
        title="Published Post", slug="published-post-detail", site=site,
        author=editor_user, status=Post.PostStatus.PUBLISHED
    )
    draft_post = Post.objects.create(
        title="Draft Post", slug="draft-post-detail", site=site,
        author=editor_user, status=Post.PostStatus.DRAFT
    )

    # Test accessing the published post
    url_published = f"/api/public/posts/{published_post.slug}/"
    response_published = api_client.get(url_published)
    assert response_published.status_code == status.HTTP_200_OK
    assert response_published.data['title'] == "Published Post"
    assert "body_text" not in response_published.data # Ensure private fields are excluded

    # Test accessing the draft post (should fail)
    url_draft = f"/api/public/posts/{draft_post.slug}/"
    response_draft = api_client.get(url_draft)
    assert response_draft.status_code == status.HTTP_404_NOT_FOUND
