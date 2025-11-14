# adminui/views/reports.py
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from reports.models import SavedReport, ReportRun
from core.models import Site
from reports.tasks import run_report_task

@login_required
def report_dashboard_view(request):
    """
    Main view for the reports dashboard page.
    """
    return render(request, 'adminui/pages/reports.html')

@login_required
def report_list_view(request):
    """
    HTMX partial view to list saved reports.
    """
    site = get_object_or_404(Site, organization=request.user.organization) # Simplified
    reports = SavedReport.objects.filter(site=site)
    return render(request, 'adminui/partials/reports/report_list.html', {'reports': reports})

@login_required
def report_runs_list_view(request):
    """
    HTMX partial view to list recent report runs.
    """
    site = get_object_or_404(Site, organization=request.user.organization) # Simplified
    report_ids = SavedReport.objects.filter(site=site).values_list('id', flat=True)
    runs = ReportRun.objects.filter(saved_report_id__in=report_ids).order_by('-created_at')[:20]
    return render(request, 'adminui/partials/reports/run_list.html', {'runs': runs})

@login_required
@require_http_methods(["GET", "POST"])
def report_create_edit_view(request, report_id=None):
    """
    Handles both creation (GET) and saving (POST) of a report.
    If report_id is provided, it's an edit.
    """
    site = get_object_or_404(Site, organization=request.user.organization)

    if report_id:
        report = get_object_or_404(SavedReport, id=report_id, site=site)
    else:
        report = None

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        dsl_query = request.POST.get('dsl_query')

        if report:
            report.name = name
            report.description = description
            report.dsl_query = dsl_query
            report.save()
        else:
            SavedReport.objects.create(
                name=name,
                description=description,
                dsl_query=dsl_query,
                site=site,
                created_by=request.user
            )

        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'reportAdded'
        return response

    return render(request, 'adminui/partials/reports/report_form.html', {'report': report})

@login_required
@require_http_methods(["POST"])
def report_trigger_run_view(request, report_id):
    """
    HTMX view to trigger a new report run.
    """
    site = get_object_or_404(Site, organization=request.user.organization)
    report = get_object_or_404(SavedReport, id=report_id, site=site)

    run = ReportRun.objects.create(
        saved_report=report,
        triggered_by=request.user,
        status=ReportRun.RunStatus.PENDING
    )

    run_report_task.delay(str(run.id))

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'reportRunStarted'
    return response
