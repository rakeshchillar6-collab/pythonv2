# adminui/urls.py
from django.urls import path
from . import views

app_name = 'adminui'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('partials/system-health/', views.system_health_partial, name='system_health_partial'),
    path('partials/integrations-health/', views.integrations_health_partial, name='integrations_health_partial'),

    # Category CRUD
    path('content/categories/', views.category_list, name='category_list'),
    path('content/categories/create/', views.category_create, name='category_create'),
    path('content/categories/<uuid:pk>/update/', views.category_update, name='category_update'),
    path('content/categories/<uuid:pk>/delete/', views.category_delete, name='category_delete'),

    # Post CRUD
    path('content/posts/', views.post_list, name='post_list'),
    path('content/posts/new/', views.post_create, name='post_create'),
    path('content/posts/<uuid:pk>/edit/', views.post_edit, name='post_edit'),
    # Editor Partials
    path('content/posts/<uuid:pk>/partials/save/', views.save_post_partial, name='save_post_partial'),
    path('content/posts/<uuid:pk>/partials/rank-me/', views.rank_me_partial, name='rank_me_partial'),
    path('content/posts/<uuid:pk>/partials/competitors/', views.competitors_partial, name='competitors_partial'),
    path('content/posts/competitors/add/', views.add_competitor, name='add_competitor'),
    # Block Partials
    path('content/posts/<uuid:pk>/blocks/faq/', views.faq_block_list, name='faq_block_list'),
    path('content/posts/blocks/faq/add/', views.add_faq_block, name='add_faq_block'),

    # Vector Search Management
    path('vector/corpora/', views.corpus_list, name='corpus_list'),
    path('vector/search/', views.search_console, name='search_console'),

    # Calendar
    path('calendar/', views.content_calendar, name='content_calendar'),

    # Reports
    path('reports/', include('adminui.urls.reports')),

    # SEO Tools
    path('seo/schema/', include('adminui.urls.schema_builder_urls')),

    # Publishing
    path('publish/', include('adminui.urls.publishing_urls')),

    # Metaphorge
    path('metaphorge/', include('adminui.urls.metaphorge_urls')),

    # Operations
    path('system/', include('adminui.urls.ops_urls')),
]
