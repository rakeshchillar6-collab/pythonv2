# tests/unit/test_core.py
import pytest
from django.db import IntegrityError
from core.models import User, Organization, Site, Role

pytestmark = pytest.mark.django_db

@pytest.fixture
def organization():
    return Organization.objects.create(name="Test Org")

@pytest.fixture
def site(organization):
    return Site.objects.create(organization=organization, name="Test Site", domain="test.com")

@pytest.fixture
def admin_role():
    return Role.objects.create(name="Admin", permissions=["*"])

@pytest.fixture
def editor_role():
    return Role.objects.create(name="Editor", permissions=["content.create", "content.edit"])

def test_create_organization():
    org = Organization.objects.create(name="New Org")
    assert org.id is not None
    assert str(org) == "New Org"

def test_create_user(organization, admin_role):
    user = User.objects.create_user(
        email="test@example.com",
        password="password123",
        organization=organization,
        role=admin_role,
        full_name="Test User"
    )
    assert user.email == "test@example.com"
    assert user.organization == organization
    assert user.role == admin_role
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password("password123")
    assert str(user) == "test@example.com"

def test_create_superuser(organization):
    admin_user = User.objects.create_superuser(
        email="admin@example.com",
        password="password123",
    )
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True

def test_user_requires_organization_and_role_for_non_superusers():
    with pytest.raises(ValueError, match="Non-superuser must have an organization and a role."):
        User.objects.create_user(email="test@test.com", password="pw")

def test_site_creation(organization):
    site = Site.objects.create(organization=organization, name="Another Site", domain="example.org")
    assert site.organization == organization
    assert str(site) == "Another Site (example.org)"

def test_role_creation():
    role = Role.objects.create(name="Viewer", permissions=["content.view"])
    assert role.name == "Viewer"
    assert role.permissions == ["content.view"]
    assert str(role) == "Viewer"

def test_user_organization_constraint(admin_role):
    # Creating a user without an organization should fail if they are not a superuser
    with pytest.raises(ValueError):
         User.objects.create_user(
            email="test@example.com",
            password="password123",
            role=admin_role,
        )

def test_duplicate_organization_name():
    Organization.objects.create(name="Unique Org")
    with pytest.raises(IntegrityError):
        Organization.objects.create(name="Unique Org")

def test_duplicate_site_domain_within_org(organization):
    Site.objects.create(organization=organization, name="Site 1", domain="unique.com")
    with pytest.raises(IntegrityError):
        Site.objects.create(organization=organization, name="Site 2", domain="unique.com")

def test_multiple_sites_same_domain_different_orgs(organization):
    other_org = Organization.objects.create(name="Other Org")
    Site.objects.create(organization=organization, name="Site 1", domain="shared.com")
    # This should be allowed
    Site.objects.create(organization=other_org, name="Site 2", domain="shared.com")
    assert Site.objects.count() == 2
