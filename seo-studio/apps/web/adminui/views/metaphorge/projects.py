# adminui/views/metaphorge/projects.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from core.models import Site
from metaphorge.models import MFProject
from metaphorge.tasks import orchestrator

@login_required
def project_dashboard(request):
    """Main view for the Metaphorge projects dashboard."""
    site = Site.objects.filter(organization=request.user.organization).first()
    projects = MFProject.objects.filter(site=site).order_by('-created_at')
    return render(request, 'adminui/pages/metaphorge/dashboard.html', {'projects': projects})

@login_required
def project_list_partial(request):
    """HTMX partial for refreshing the project list."""
    site = Site.objects.filter(organization=request.user.organization).first()
    projects = MFProject.objects.filter(site=site).order_by('-created_at')
    return render(request, 'adminui/partials/metaphorge/project_list.html', {'projects': projects})

@login_required
def project_create_modal(request):
    """Renders the modal form for creating a new project."""
    return render(request, 'adminui/partials/metaphorge/project_form.html')

@login_required
def project_create(request):
    """Handles the creation of a new Metaphorge project."""
    site = Site.objects.filter(organization=request.user.organization).first()

    # Basic creation from form; config would be more complex in a real app
    MFProject.objects.create(
        site=site,
        name=request.POST.get('name'),
        description=request.POST.get('description'),
        created_by=request.user,
        config={ # Simplified config for now
            'depth': int(request.POST.get('depth', 1)),
            'max_suggest': 10,
            'cluster_threshold': 3,
        }
    )

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'projectListChanged'
    return response

# --- Project Control Actions ---
def _project_action(project_id, action_func):
    action_func(project_id)
    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'projectListChanged'
    return response

@login_required
def project_start(request, project_id):
    return _project_action(project_id, orchestrator.start_project)

@login_required
def project_pause(request, project_id):
    return _project_action(project_id, orchestrator.pause_project)

@login_required
def project_resume(request, project_id):
    return _project_action(project_id, orchestrator.resume_project)
