# tests/unit/test_schema_builder.py
import pytest
from unittest.mock import patch
import json

from core.models import Site, Organization
from content.models import Post, Category
from schema_builder.models import SchemaTemplate, SchemaAssignment, SchemaRenderCache
from schema_builder.services.renderer import render_schema_for_post
from schema_builder.services.validator import SchemaValidator

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="Test Org")
    return Site.objects.create(organization=org, name="Test Site", domain="test.com")

@pytest.fixture
def post(site):
    return Post.objects.create(site=site, title="Test Post", slug="test-post", type="article")

@pytest.fixture
def article_template(site):
    return SchemaTemplate.objects.create(
        site=site,
        name="Article Template",
        schema_type="Article",
        template={
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "{{ post.title }}",
            "author": {
                "@type": "Person",
                "name": "{{ author.full_name }}"
            }
        }
    )

def test_render_schema_for_post(post, article_template):
    # Assign the template globally
    SchemaAssignment.objects.create(site=post.site, template=article_template, target_type='global')

    rendered_jsonld = render_schema_for_post(post.id)

    assert len(rendered_jsonld) == 1
    article_schema = rendered_jsonld[0]
    assert article_schema['@type'] == 'Article'
    assert article_schema['headline'] == 'Test Post'
    assert 'author' in article_schema

def test_schema_caching(post, article_template):
    SchemaAssignment.objects.create(site=post.site, template=article_template, target_type='global')

    # First render
    with patch('schema_builder.services.renderer.SchemaRenderer._render_template') as mock_render:
        mock_render.return_value = {"@type": "Article"}
        render_schema_for_post(post.id)
        assert mock_render.call_count == 1

    # Second render should hit the cache
    with patch('schema_builder.services.renderer.SchemaRenderer._render_template') as mock_render:
        render_schema_for_post(post.id)
        assert mock_render.call_count == 0

    # Invalidate cache by updating post
    post.title = "Updated Title"
    post.save()

    # Third render should miss the cache
    with patch('schema_builder.services.renderer.SchemaRenderer._render_template') as mock_render:
        mock_render.return_value = {"@type": "Article"}
        render_schema_for_post(post.id)
        assert mock_render.call_count == 1

def test_validator_success(post, article_template):
    rendered = {
        "@type": "Article",
        "headline": "A Headline",
        "author": "Someone",
        "datePublished": "2023-01-01T12:00:00Z"
    }
    validator = SchemaValidator(post, article_template, rendered)
    is_valid, errors = validator.validate()
    assert is_valid is True
    assert len(errors) == 0

def test_validator_missing_property(post, article_template):
    rendered = {
        "@type": "Article",
        "author": "Someone"
    }
    validator = SchemaValidator(post, article_template, rendered)
    is_valid, errors = validator.validate()
    assert is_valid is False
    assert len(errors) > 0
    assert "Missing required property" in errors[0]['error']
