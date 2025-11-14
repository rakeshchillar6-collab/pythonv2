# adminui/views.py
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Max
from django.utils import timezone

from content.models import Post, Category, CompetitorURL, FaqBlock
from vectorsearch.models import Corpus
from calendar.models import ContentTask
from .forms import CategoryForm, CorpusForm, PostForm, FaqBlockForm
from integrations.health import get_system_health, get_connectors_health
from core.auth import require_roles
from rankme import evaluate_post
from rankme.competitors import fetch_competitor_data

# ... (Previous views: dashboard, health, category, corpus, post, rank-me, competitors, faq) ...
def htmx_response_with_message(response: HttpResponse, message: str) -> HttpResponse:
    response['HX-Trigger'] = f'{{"showMessage": "{message}"}}'
    return response

# --- Calendar Views ---

@login_required
@require_roles('admin', 'editor')
def content_calendar(request: HttpRequest) -> HttpResponse:
    """Displays the content calendar view."""
    # Simplified: Get tasks for the user's first site
    site = request.user.sites.first()
    tasks = ContentTask.objects.filter(post__site=site) if site else ContentTask.objects.none()

    # Kanban columns
    columns = {
        'TODO': 'To Do',
        'DOING': 'In Progress',
        'DONE': 'Done'
    }

    tasks_by_column = {state: list(tasks.filter(state=state)) for state in columns.keys()}

    return render(request, 'adminui/calendar/calendar_view.html', {
        'columns': columns,
        'tasks_by_column': tasks_by_column
    })
