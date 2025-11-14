# adminui/views/publishing/jobs.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from core.models import Site
from publishing.models import PublishJob
from publishing.tasks import execute_publish_job

@login_required
def job_dashboard(request):
    """Main view for the publish jobs dashboard."""
    site = Site.objects.filter(organization=request.user.organization).first()
    jobs = PublishJob.objects.filter(destination__site=site).order_by('-created_at')[:50]
    return render(request, 'adminui/pages/publishing/jobs.html', {'jobs': jobs})

@login_required
def job_list_partial(request):
    """HTMX partial for refreshing the job list."""
    site = Site.objects.filter(organization=request.user.organization).first()
    jobs = PublishJob.objects.filter(destination__site=site).order_by('-created_at')[:50]
    return render(request, 'adminui/partials/publishing/job_list.html', {'jobs': jobs})

@login_required
def job_detail_modal(request, job_id):
    """HTMX partial for showing job details in a modal."""
    site = Site.objects.filter(organization=request.user.organization).first()
    job = get_object_or_404(PublishJob, id=job_id, destination__site=site)
    return render(request, 'adminui/partials/publishing/job_detail.html', {'job': job})

@login_required
def job_retry(request, job_id):
    """Action to retry a failed job."""
    site = Site.objects.filter(organization=request.user.organization).first()
    job = get_object_or_404(PublishJob, id=job_id, destination__site=site)

    # Reset state and re-queue
    job.status = PublishJob.Status.PENDING
    job.attempts = 0
    job.error_message = ""
    job.save()

    execute_publish_job.delay(str(job.id))

    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'jobListChanged'
    return response
