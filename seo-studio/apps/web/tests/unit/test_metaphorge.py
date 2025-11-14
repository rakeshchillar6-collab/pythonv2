# tests/unit/test_metaphorge.py
import pytest
from unittest.mock import patch, MagicMock

from core.models import Site, Organization, User
from metaphorge.models import MFProject, MFSeed, MFCombo
from metaphorge.tasks import orchestrator, combine

pytestmark = pytest.mark.django_db

@pytest.fixture
def site():
    org = Organization.objects.create(name="Test Org")
    return Site.objects.create(organization=org, name="Test Site", domain="test.com")

@pytest.fixture
def user(site):
    return User.objects.create_user(email="test@test.com", password="pw", organization=site.organization)

@pytest.fixture
def mf_project(site, user):
    return MFProject.objects.create(
        site=site,
        name="Test Project",
        created_by=user,
        config={
            "letters": "en",
            "numbers_range": [1, 2],
            "before_after": [["before", "after"]],
        }
    )

def test_combine_seeds_task(mf_project):
    """Tests that the combine task creates all expected combo patterns."""
    seed = MFSeed.objects.create(project=mf_project, text="keyword")

    combine.combine_seeds_task(mf_project.id)

    combos = MFCombo.objects.filter(project=mf_project)
    patterns = {c.pattern for c in combos}

    assert 'space' in patterns
    assert 'space_q' in patterns
    assert 'space_letters' in patterns
    assert 'space_numbers' in patterns
    assert 'before_after' in patterns

    assert MFCombo.objects.filter(pattern='space_letters').count() == 26
    assert MFCombo.objects.filter(pattern='space_numbers').count() == 2
    assert MFCombo.objects.filter(pattern='before_after').count() == 1

@patch('metaphorge.tasks.orchestrator.STAGE_TASK_MAP')
def test_orchestrator_start_and_advance(mock_stage_map, mf_project):
    """Tests the basic state machine of the orchestrator."""

    # Mock the task functions
    mock_combine_task = MagicMock()
    mock_expand_task = MagicMock()

    # Configure the mock map to return our mock tasks
    # We use .s() to simulate the celery signature object
    mock_stage_map.get.side_effect = [
        mock_combine_task.s(),
        mock_expand_task.s(),
    ]

    # 1. Start the project
    orchestrator.start_project(mf_project.id)

    # It should have called the first stage task (combine)
    mock_combine_task.s.assert_called_once_with(project_id=str(mf_project.id))

    # 2. Simulate the advance_stage task being called after 'combine' completes
    orchestrator.advance_stage_task(mf_project.id)

    mf_project.refresh_from_db()
    assert mf_project.stage == MFProject.Stage.EXPAND

    # 3. Trigger the orchestrator again for the new stage
    orchestrator.run_metaphorge_project(mf_project.id)

    # It should have called the second stage task (expand)
    mock_expand_task.s.assert_called_once_with(project_id=str(mf_project.id))

def test_orchestrator_pause_and_resume(mf_project):
    """Tests that a paused project does not proceed."""
    with patch('metaphorge.tasks.orchestrator.run_metaphorge_project.delay') as mock_run:

        # Pause the project
        orchestrator.pause_project(mf_project.id)
        mf_project.refresh_from_db()
        assert mf_project.status == MFProject.Status.PAUSED

        # Try to run it (should exit early)
        orchestrator.run_metaphorge_project(mf_project.id)
        mock_run.assert_not_called()

        # Resume the project
        orchestrator.resume_project(mf_project.id)
        mf_project.refresh_from_db()
        assert mf_project.status == MFProject.Status.IDLE

        # run_metaphorge_project is called by resume, so the pipeline should now start
        mock_run.assert_called_once_with(project_id=mf_project.id)
