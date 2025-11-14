# adminui/views/schema_builder/assignments.py
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from core.models import Site
from schema_builder.models import SchemaAssignment, SchemaTemplate
from content.models import Category

@login_required
def assignment_dashboard(request):
    """Main view for the schema assignments dashboard page."""
    site = Site.objects.filter(organization=request.user.organization).first()
    assignments = SchemaAssignment.objects.filter(site=site)
    templates = SchemaTemplate.objects.filter(site=site)
    categories = Category.objects.filter(site=site)

    context = {
        'assignments': assignments,
        'templates': templates,
        'categories': categories,
        'post_types': Post.PostType.choices, # Assumes PostType enum exists
    }
    return render(request, 'adminui/pages/schema_builder/assignments.html', context)

@login_required
@require_http_methods(["POST"])
def assignment_create(request):
    site = Site.objects.filter(organization=request.user.organization).first()

    template_id = request.POST.get('template')
    target_type = request.POST.get('target_type')
    post_type = request.POST.get('post_type')
    category_id = request.POST.get('category')
    priority = request.POST.get('priority', 10)

    SchemaAssignment.objects.create(
        site=site,
        template_id=template_id,
        target_type=target_type,
        post_type=post_type if target_type == 'post_type' else None,
        category_id=category_id if target_type == 'category' else None,
        priority=priority
    )

    assignments = SchemaAssignment.objects.filter(site=site)
    return render(request, 'adminui/partials/schema_builder/assignment_list.html', {'assignments': assignments})

@login_required
@require_http_methods(["DELETE"])
def assignment_delete(request, assignment_id):
    site = Site.objects.filter(organization=request.user.organization).first()
    assignment = get_object_or_404(SchemaAssignment, id=assignment_id, site=site)
    assignment.delete()

    return HttpResponse(status=200) # Target the row for deletion in the template
