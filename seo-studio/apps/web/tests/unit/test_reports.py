# tests/unit/test_reports.py
import pytest
from datetime import date, timedelta
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, call

from reports.services.report_runner import run_report
from reports.services.dsl_parser import parse_dsl
from reports.models import SavedReport, ReportRun
from content.models import Post, Category
from core.models import User, Site, Organization

pytestmark = pytest.mark.django_db

# --- DSL Parser Tests ---
def test_dsl_parser_simple_query():
    query = 'FROM posts SELECT id, title, status WHERE status = "published" ORDER BY created_at DESC LIMIT 10'
    parsed = parse_dsl(query)
    assert parsed['model'] == 'posts'
    assert parsed['fields'] == ['id', 'title', 'status']
    assert parsed['filters'] == [{'field': 'status', 'operator': '=', 'value': 'published'}]
    assert parsed['order_by'] == {'field': 'created_at', 'direction': 'DESC'}
    assert parsed['limit'] == 10

def test_dsl_parser_date_filter():
    query = 'FROM posts SELECT title WHERE published_at > "30d"'
    parsed = parse_dsl(query)
    assert parsed['filters'][0]['field'] == 'published_at'
    assert parsed['filters'][0]['operator'] == '>'
    # The value should be a date object
    assert isinstance(parsed['filters'][0]['value'], date)
    assert parsed['filters'][0]['value'] == (timezone.now() - timedelta(days=30)).date()

def test_dsl_parser_invalid_model():
    with pytest.raises(ValueError, match="Invalid model 'users' specified"):
        parse_dsl('FROM users SELECT id')

def test_dsl_parser_invalid_field():
    with pytest.raises(ValueError, match="Invalid field 'password' for model 'posts'"):
        parse_dsl('FROM posts SELECT password')

def test_dsl_parser_malformed_query():
    with pytest.raises(ValueError, match="Invalid query structure"):
        parse_dsl('SELECT id FROM posts')

# --- Report Runner Tests ---

@pytest.fixture
def site():
    org = Organization.objects.create(name="Report Org")
    return Site.objects.create(organization=org, name="Report Site", domain="https://report.com")

@pytest.fixture
def user(site):
    return User.objects.create_user(email="reporter@test.com", password="pw", organization=site.organization)

@pytest.fixture
def posts(site):
    Post.objects.create(site=site, title="Post 1", status='published', published_at=timezone.now() - timedelta(days=5))
    Post.objects.create(site=site, title="Post 2", status='draft', published_at=timezone.now() - timedelta(days=10))
    Post.objects.create(site=site, title="Post 3", status='published', published_at=timezone.now() - timedelta(days=15))

@pytest.fixture
def saved_report(site, user):
    return SavedReport.objects.create(
        site=site,
        created_by=user,
        name="Test Report",
        dsl_query='FROM posts SELECT title, status, published_at WHERE status = "published" ORDER BY published_at ASC'
    )

def test_run_report_success(saved_report, posts):
    report_run = ReportRun.objects.create(saved_report=saved_report, triggered_by=saved_report.created_by)

    with patch('reports.services.report_runner.default_storage.save') as mock_save:
        mock_save.return_value = 'reports/test.csv'
        run_report(str(report_run.id))

    report_run.refresh_from_db()

    assert report_run.status == ReportRun.RunStatus.COMPLETED
    assert report_run.finished_at is not None
    assert report_run.result_file.name == 'reports/test.csv'

    # Check that the file was saved with the correct content
    assert mock_save.call_count == 1
    filename, content_file = mock_save.call_args[0]
    content = content_file.read().decode('utf-8')

    assert 'title,status,published_at' in content
    assert 'Post 1,published' in content
    assert 'Post 3,published' in content
    assert 'Post 2,draft' not in content # Should be filtered out

def test_run_report_invalid_dsl(saved_report):
    saved_report.dsl_query = "FROM posts SELECT invalid_field"
    saved_report.save()
    report_run = ReportRun.objects.create(saved_report=saved_report, triggered_by=saved_report.created_by)

    run_report(str(report_run.id))

    report_run.refresh_from_db()
    assert report_run.status == ReportRun.RunStatus.FAILED
    assert "Invalid field 'invalid_field'" in report_run.log

def test_run_report_no_results(saved_report):
    Post.objects.all().delete()
    report_run = ReportRun.objects.create(saved_report=saved_report, triggered_by=saved_report.created_by)

    with patch('reports.services.report_runner.default_storage.save') as mock_save:
        run_report(str(report_run.id))

    report_run.refresh_from_db()
    assert report_run.status == ReportRun.RunStatus.COMPLETED
    assert mock_save.call_count == 1
    content = mock_save.call_args[0][1].read().decode('utf-8')
    assert 'title,status,published_at' in content
    # Should only contain the header
    assert len(content.strip().split('\\n')) == 1
