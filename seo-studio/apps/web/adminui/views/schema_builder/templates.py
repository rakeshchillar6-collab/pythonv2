# adminui/views/schema_builder/templates.py
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from core.models import Site
from schema_builder.models import SchemaTemplate

@login_required
def template_dashboard(request):
    """Main view for the schema templates dashboard page."""
    return render(request, 'adminui/pages/schema_builder/templates.html')

@login_required
def template_list_partial(request):
    """HTMX partial view for listing schema templates."""
    site = Site.objects.filter(organization=request.user.organization).first()
    templates = SchemaTemplate.objects.filter(site=site)
    return render(request, 'adminui/partials/schema_builder/template_list.html', {'templates': templates})

@login_required
@require_http_methods(["GET", "POST"])
def template_create_edit(request, template_id=None):
    """Handles both creation and editing of a schema template in a modal."""
    site = Site.objects.filter(organization=request.user.organization).first()

    if template_id:
        template = get_object_or_404(SchemaTemplate, id=template_id, site=site)
    else:
        template = None

    if request.method == 'POST':
        name = request.POST.get('name')
        schema_type = request.POST.get('schema_type')
        template_json = request.POST.get('template')

        # Basic validation
        import json
        try:
            template_data = json.loads(template_json)
        except json.JSONDecodeError:
            # Handle error, maybe return a message to the user
            return HttpResponse("Invalid JSON in template.", status=400)

        if template:
            template.name = name
            template.schema_type = schema_type
            template.template = template_data
            template.save()
        else:
            SchemaTemplate.objects.create(
                site=site,
                name=name,
                schema_type=schema_type,
                template=template_data
            )

        # Trigger a refresh of the list on the page
        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'schemaTemplateChanged'
        return response

    return render(request, 'adminui/partials/schema_builder/template_form.html', {'template': template})

@login_required
@require_http_methods(["DELETE"])
def template_delete(request, template_id):
    site = Site.objects.filter(organization=request.user.organization).first()
    template = get_object_or_404(SchemaTemplate, id=template_id, site=site)
    template.delete()

    # Trigger a refresh of the list
    response = HttpResponse(status=204)
    response['HX-Trigger'] = 'schemaTemplateChanged'
    return response
