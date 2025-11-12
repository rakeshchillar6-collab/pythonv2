# adminui/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from content.models import Post, Category
from .forms import CategoryForm

# Utility function to prepare response with message header
def htmx_message_response(request, template_name, context, message):
    response = render(request, template_name, context)
    response['HX-Trigger'] = '{"showMessage": "' + message + '"}' # A simple way to trigger events
    response['X-Message'] = message # Custom header for simple toast
    return response

@login_required
def dashboard(request):
    post_count = Post.objects.count()
    category_count = Category.objects.count()
    context = {
        'post_count': post_count,
        'category_count': category_count,
    }
    return render(request, 'adminui/dashboard.html', context)

@login_required
def health_check(request):
    return HttpResponse('<span class="text-green-500 font-bold">● آنلاین</span>')

# Category CRUD Views
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'adminui/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            categories = Category.objects.all()
            return htmx_message_response(
                request,
                'adminui/partials/category_table.html',
                {'categories': categories},
                'دسته‌بندی با موفقیت ایجاد شد.'
            )
    else:
        form = CategoryForm()

    return render(request, 'adminui/partials/category_form.html', {'form': form})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            categories = Category.objects.all()
            return htmx_message_response(
                request,
                'adminui/partials/category_table.html',
                {'categories': categories},
                'دسته‌بندی با موفقیت ویرایش شد.'
            )
    else:
        form = CategoryForm(instance=category)

    return render(request, 'adminui/partials/category_form.html', {'form': form, 'category': category})

@require_POST
@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    categories = Category.objects.all()
    return htmx_message_response(
        request,
        'adminui/partials/category_table.html',
        {'categories': categories},
        'دسته‌بندی با موفقیت حذف شد.'
    )
