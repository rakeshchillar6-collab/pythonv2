# adminui/views.py
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from content.models import Post, Category
from vectorsearch.models import Corpus
from .forms import CategoryForm, CorpusForm, PostForm
from integrations.health import get_system_health, get_connectors_health
from core.auth import require_roles
from rankme import evaluate_post

# ... (Dashboard, Health, Category, Corpus, Search Console views remain the same) ...
# --- Post CRUD Views ---

@login_required
@require_roles('admin', 'editor')
def post_list(request: HttpRequest) -> HttpResponse:
    posts = Post.objects.all() # Simplified for now
    return render(request, 'adminui/content/post_list.html', {'posts': posts})

@login_required
@require_roles('admin', 'editor')
def post_create(request: HttpRequest) -> HttpResponse:
    # This view now just redirects to the editor for a new, unsaved post instance
    # The actual creation happens on the first save in the editor
    post_type = request.GET.get('type', Post.PostType.ARTICLE).upper()
    # Create an in-memory instance
    post = Post(type=post_type, author=request.user, title="عنوان پیش‌نویس")
    # In a real app, you might save a minimal draft here and get a PK
    # For now, let's assume we create it and redirect.
    post.site = SiteProfile.objects.first() # Placeholder
    post.slug = f"draft-{uuid.uuid4()}" # Placeholder
    post.save()
    return HttpResponse(status=204, headers={'HX-Redirect': reverse('adminui:post_edit', args=[post.pk])})

@login_required
@require_roles('admin', 'editor')
def post_edit(request: HttpRequest, pk: str) -> HttpResponse:
    """The main editor layout view."""
    post = get_object_or_404(Post, pk=pk)
    form = PostForm(instance=post)
    return render(request, 'adminui/content/editor_layout.html', {'post': post, 'form': form})

# --- Editor Partials ---

@require_POST
@login_required
@require_roles('admin', 'editor')
def save_post_partial(request: HttpRequest, pk: str) -> HttpResponse:
    """Saves the post form and triggers other partials to update."""
    post = get_object_or_404(Post, pk=pk)
    form = PostForm(request.POST, instance=post)
    if form.is_valid():
        form.save()
        response = HttpResponse("ذخیره شد!", status=200)
        # Trigger the Rank-Me panel to reload
        response['HX-Trigger'] = '{"reloadRankMe": "true"}'
        return response
    else:
        # Handle form errors (e.g., return the form with errors)
        return render(request, 'adminui/content/partials/post_form_errors.html', {'form': form}, status=400)


from rankme.competitors import fetch_competitor_data
from content.models import CompetitorURL
from django.utils import timezone

@login_required
@require_roles('admin', 'editor')
def rank_me_partial(request: HttpRequest, pk: str) -> HttpResponse:
    """Evaluates the (saved) post and returns the Rank-Me panel."""
    post = get_object_or_404(Post, pk=pk)
    evaluation = evaluate_post(post.pk)
    return render(request, 'adminui/content/partials/rank_me_panel.html', {'evaluation': evaluation, 'post': post})

@login_required
@require_roles('admin', 'editor')
def competitors_partial(request: HttpRequest, pk: str) -> HttpResponse:
    """Renders the competitors panel."""
    post = get_object_or_404(Post, pk=pk,_prefetched_objects_cache={})
    return render(request, 'adminui/content/partials/competitors_panel.html', {'post': post})

@require_POST
@login_required
@require_roles('admin', 'editor')
def add_competitor(request: HttpRequest) -> HttpResponse:
    """Fetches data for a new competitor URL and returns the updated list."""
    post_id = request.POST.get('post_id')
    url = request.POST.get('url')
    post = get_object_or_404(Post, pk=post_id)

    if not url:
        # Handle error, maybe return a toast message
        return HttpResponse("URL cannot be empty.", status=400)

    data = fetch_competitor_data(url)

    if data.get('error'):
        # Handle fetch error, maybe return a toast
        return HttpResponse(f"Error: {data['error']}", status=400)

    CompetitorURL.objects.create(
        post=post,
        url=url,
        word_count=data['word_count'],
        headings_json=data['headings_json'],
        last_fetch_at=timezone.now()
    )

    # Return the updated list of competitors
    return render(request, 'adminui/content/partials/competitors_panel.html', {'post': post})

# --- Block Views ---

@login_required
@require_roles('admin', 'editor')
def faq_block_list(request: HttpRequest, pk: str) -> HttpResponse:
    """Renders the list of FAQ blocks for a post."""
    post = get_object_or_404(Post, pk=pk)
    form = FaqBlockForm()
    return render(request, 'adminui/content/partials/faq_blocks.html', {'post': post, 'form': form})

@require_POST
@login_required
@require_roles('admin', 'editor')
def add_faq_block(request: HttpRequest) -> HttpResponse:
    """Adds a new FAQ block to a post and returns the updated list."""
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, pk=post_id)
    form = FaqBlockForm(request.POST)
    if form.is_valid():
        faq = form.save(commit=False)
        faq.post = post
        # Set order to be the last one
        last_order = post.faq_blocks.aggregate(models.Max('order'))['order__max'] or 0
        faq.order = last_order + 1
        faq.save()

    # Return the updated list
    form = FaqBlockForm() # Empty form for the next entry
    return render(request, 'adminui/content/partials/faq_blocks.html', {'post': post, 'form': form})
