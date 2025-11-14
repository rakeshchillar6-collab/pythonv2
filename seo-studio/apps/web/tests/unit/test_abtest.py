# tests/unit/test_abtest.py
import pytest
from unittest.mock import MagicMock, patch
from django.http import HttpResponse
from django.test import RequestFactory

from abtest.models import ABTest, ABTestVariant
from abtest.middleware import ABTestMiddleware
from core.models import Site, Organization
from content.models import Post

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="AB Test Org")
    return Site.objects.create(organization=org, name="AB Test Site", domain="abtest.com")

@pytest.fixture
def post(site):
    return Post.objects.create(site=site, title="Original Post", slug="test-post", full_url="https://abtest.com/test-post")

@pytest.fixture
def variant_post(site):
    return Post.objects.create(site=site, title="Variant Post", slug="variant-post", full_url="https://abtest.com/variant-post")

@pytest.fixture
def ab_test(site, post, variant_post):
    test = ABTest.objects.create(
        site=site,
        name="Test Homepage",
        target_page_url_regex="^/$",
        status=ABTest.Status.RUNNING,
        traffic_percentage=100
    )
    ABTestVariant.objects.create(test=test, post=post, is_control=True, split_percentage=50)
    ABTestVariant.objects.create(test=test, post=variant_post, is_control=False, split_percentage=50)
    return test

@pytest.fixture
def factory():
    return RequestFactory()

@pytest.fixture
def middleware():
    # A dummy get_response function
    return ABTestMiddleware(lambda req: HttpResponse("Original Response"))

def test_abtest_model_creation(site, post):
    test = ABTest.objects.create(
        site=site,
        name="Test 1",
        target_page_url_regex="/test-page/.*",
        status=ABTest.Status.DRAFT
    )
    assert str(test) == "Test 1"

def test_middleware_no_match(middleware, factory, site):
    request = factory.get("/another-page/")
    request.site = site  # Middleware expects site to be attached

    response = middleware(request)

    assert response.status_code == 200
    assert response.content == b"Original Response"
    assert not hasattr(request, 'ab_test_variant')

def test_middleware_inactive_test(middleware, factory, site, ab_test):
    ab_test.status = ABTest.Status.COMPLETED
    ab_test.save()

    request = factory.get("/")
    request.site = site

    response = middleware(request)
    assert not hasattr(request, 'ab_test_variant')

def test_middleware_traffic_allocation_miss(middleware, factory, site, ab_test):
    ab_test.traffic_percentage = 0  # No traffic
    ab_test.save()

    request = factory.get("/")
    request.site = site

    response = middleware(request)
    assert not hasattr(request, 'ab_test_variant')

@patch('abtest.middleware.render')
def test_middleware_variant_assignment_and_render(mock_render, middleware, factory, site, ab_test):
    mock_render.return_value = HttpResponse("Variant Response")
    request = factory.get("/")
    request.site = site
    request.COOKIES = {} # Ensure no pre-existing cookie

    # We can't control the random assignment, so we'll check that one of the variants is assigned
    response = middleware(request)

    assert hasattr(request, 'ab_test_variant')
    variant_assigned = request.ab_test_variant

    assert variant_assigned.test == ab_test

    if variant_assigned.is_control:
        # If control is chosen, the original response should be returned
        assert response.content == b"Original Response"
        assert not mock_render.called
    else:
        # If variant is chosen, render should be called with the variant post
        assert response.content == b"Variant Response"
        mock_render.assert_called_once()
        render_args = mock_render.call_args[0]
        assert render_args[0] == request
        assert "post" in render_args[2]
        assert render_args[2]["post"] == variant_assigned.post

    # Check that a cookie was set
    assert f"ab_test_{ab_test.id}" in response.cookies

def test_middleware_cookie_respects_assignment(middleware, factory, site, ab_test):
    variant = ab_test.variants.get(is_control=False)
    request = factory.get("/")
    request.site = site
    request.COOKIES = {f"ab_test_{ab_test.id}": str(variant.id)}

    with patch('abtest.middleware.render') as mock_render:
        mock_render.return_value = HttpResponse("Variant Response")
        response = middleware(request)

    assert hasattr(request, 'ab_test_variant')
    assert request.ab_test_variant == variant
    # Ensure the variant is rendered, not the control
    assert response.content == b"Variant Response"
