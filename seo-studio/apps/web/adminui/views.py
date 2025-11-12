# adminui/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST
from content.models import Post, Category
from .forms import CategoryForm
from integrations.health import get_system_health, get_connectors_health
from core.auth import require_roles

# Utility to add a toast message header to an HTMX response
def htmx_response_with_message(response: HttpResponse, message: str) -> HttpResponse:
    response['HX-Trigger'] = f'{{"showMessage": "{message}"}}'
    return response

@login_required
@require_roles('admin', 'editor')
def dashboard(request: HttpRequest) -> HttpResponse:
    """Displays the main admin dashboard."""
    context = {
        'post_count': Post.objects.count(),
        'category_count': Category.objects.count(),
    }
    return render(request, 'adminui/dashboard.html', context)

# --- Health Partials for Dashboard ---
@login_required
@require_roles('admin', 'editor')
def system_health_partial(request: HttpRequest) -> HttpResponse:
    """HTMX partial view for the system health card."""
    health_data = get_system_health()
    return render(request, 'adminui/partials/system_health_partial.html', {'health_data': health_data})

@login_required
@require_roles('admin', 'editor')
def integrations_health_partial(request: HttpRequest) -> HttpResponse:
    """HTMX partial view for the integrations health card."""
    connectors_data = get_connectors_health()
    return render(request, 'adminui/partials/integrations_health_partial.html', {'connectors_data': connectors_data})

# --- Category CRUD Views ---
@login_required
@require_roles('admin', 'editor')
def category_list(request: HttpRequest) -> HttpResponse:
    """Displays the list of categories."""
    categories = Category.objects.all()
    return render(request, 'adminui/category_list.html', {'categories': categories})

@login_required
@require_roles('admin', 'editor')
def category_create(request: HttpRequest) -> HttpResponse:
    """Handles both GET (show form) and POST (save form) for creating a category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            categories = Category.objects.all()
            response = render(request, 'adminui/partials/category_table.html', {'categories': categories})
            return htmx_response_with_message(response, 'دسته‌بندی با موفقیت ایجاد شد.')
    else:
        form = CategoryForm()

    return render(request, 'adminui/partials/category_form.html', {'form': form})

@login_required
@require_roles('admin', 'editor')
def category_update(request: HttpRequest, pk: str) -> HttpResponse:
    """Handles both GET (show form) and POST (save form) for updating a category."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            categories = Category.objects.all()
            response = render(request, 'adminui/partials/category_table.html', {'categories': categories})
            return htmx_response_with_message(response, 'دسته‌بندی با موفقیت ویرایش شد.')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'adminui/partials/category_form.html', {'form': form, 'category': category})

@require_POST
@login_required
@require_roles('admin', 'editor')
def category_delete(request: HttpRequest, pk: str) -> HttpResponse:
    """Handles POST request to delete a category."""
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    categories = Category.objects.all()
    response = render(request, 'adminui/partials/category_table.html', {'categories': categories})
    return htmx_response_with_message(response, 'دسته‌بندی با موفقیت حذف شد.')
