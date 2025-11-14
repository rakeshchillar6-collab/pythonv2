# tests/unit/test_integrations.py
import pytest
from unittest.mock import patch
from django.core.exceptions import ValidationError

from integrations.models import GSCProperty, GAProperty
from core.models import Site, Organization
from integrations.services.gsc_client import GSCClient

pytestmark = pytest.mark.django_db

@pytest.fixture
def organization():
    return Organization.objects.create(name="Test Org")

@pytest.fixture
def site(organization):
    return Site.objects.create(organization=organization, name="Test Site", domain="https://example.com")

def test_create_gsc_property(site):
    gsc_prop = GSCProperty.objects.create(
        site=site,
        gsc_site_url="sc-domain:example.com",
        credentials={"token": "fake-token"}
    )
    assert gsc_prop.site == site
    assert gsc_prop.gsc_site_url == "sc-domain:example.com"
    assert gsc_prop.is_active is True
    assert str(gsc_prop) == "sc-domain:example.com"

def test_create_ga_property(site):
    ga_prop = GAProperty.objects.create(
        site=site,
        property_id="properties/12345678",
        credentials={"key": "secret-key"}
    )
    assert ga_prop.site == site
    assert ga_prop.property_id == "properties/12345678"
    assert str(ga_prop) == "properties/12345678"

def test_gsc_property_uniqueness_for_site(site):
    GSCProperty.objects.create(site=site, gsc_site_url="sc-domain:example.com")
    with pytest.raises(ValidationError):
        prop2 = GSCProperty(site=site, gsc_site_url="sc-domain:another.com")
        prop2.full_clean() # `unique=True` is checked at the model validation level

def test_ga_property_uniqueness_for_site(site):
    GAProperty.objects.create(site=site, property_id="properties/123")
    with pytest.raises(ValidationError):
        prop2 = GAProperty(site=site, property_id="properties/456")
        prop2.full_clean()

@patch('integrations.services.gsc_client.GSCClient.test_connection')
def test_gsc_property_test_connection_success(mock_test_connection, site):
    mock_test_connection.return_value = (True, "Connection successful")
    gsc_prop = GSCProperty.objects.create(
        site=site,
        gsc_site_url="sc-domain:example.com",
        credentials={"token": "fake-token"}
    )
    is_ok, message = gsc_prop.test_connection()
    assert is_ok is True
    assert message == "Connection successful"
    mock_test_connection.assert_called_once()

@patch('integrations.services.gsc_client.GSCClient.test_connection')
def test_gsc_property_test_connection_failure(mock_test_connection, site):
    mock_test_connection.return_value = (False, "Invalid credentials")
    gsc_prop = GSCProperty.objects.create(
        site=site,
        gsc_site_url="sc-domain:example.com",
        credentials={"token": "bad-token"}
    )
    is_ok, message = gsc_prop.test_connection()
    assert is_ok is False
    assert message == "Invalid credentials"
    mock_test_connection.assert_called_once()

# Mock GSC Client tests
def test_gsc_client_initialization():
    client = GSCClient(credentials={"token": "abc"})
    assert client.credentials == {"token": "abc"}

@patch('integrations.services.gsc_client.GSCClient.fetch_performance_data')
def test_mock_gsc_client_returns_data(mock_fetch):
    # This tests our mock implementation, which is important for predictable test data
    expected_data = [{'keys': ['2024-10-01', 'https://example.com/page1'], 'clicks': 100, 'impressions': 2000, 'ctr': 0.05, 'position': 1.5}]
    mock_fetch.return_value = expected_data

    client = GSCClient(credentials={})
    data = client.fetch_performance_data(property_url="sc-domain:example.com", start_date="2024-10-01", end_date="2024-10-01")

    assert data == expected_data
    mock_fetch.assert_called_once()
