# adminui/views/publishing/destinations.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import json

from core.models import Site
from publishing.models import PublishDestination

@login_required
def destination_dashboard(request):
    """Main view for the publishing destinations dashboard."""
    site = Site.objects.filter(organization=request.user.organization).first()
    destinations = PublishDestination.objects.filter(site=site)
    destination_types = PublishDestination.DestinationType.choices

    context = {
        'destinations': destinations,
        'destination_types': destination_types,
    }
    return render(request, 'adminui/pages/publishing/destinations.html', context)

@login_required
def destination_create(request):
    """Creates a new publishing destination."""
    site = Site.objects.filter(organization=request.user.organization).first()

    name = request.POST.get('name')
    type = request.POST.get('type')

    # Simple config handling from form POST data
    config = {}
    if type == 'headless_push':
        config['endpoint_url'] = request.POST.get('endpoint_url')
        config['auth_header_template'] = request.POST.get('auth_header_template')
        config['api_key'] = request.POST.get('api_key') # In real app, use secrets manager
    elif type == 'static_export':
        config['target_root'] = request.POST.get('target_root')
        config['asset_policy'] = request.POST.get('asset_policy')

    PublishDestination.objects.create(
        site=site,
        name=name,
        type=type,
        config=config
    )

    destinations = PublishDestination.objects.filter(site=site)
    return render(request, 'adminui/partials/publishing/destination_list.html', {'destinations': destinations})

@login_required
def destination_delete(request, dest_id):
    site = Site.objects.filter(organization=request.user.organization).first()
    destination = get_object_or_404(PublishDestination, id=dest_id, site=site)
    destination.delete()

    return HttpResponse(status=200)
