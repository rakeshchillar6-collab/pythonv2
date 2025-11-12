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

    # Vector Search Management
    path('vector/corpora/', views.corpus_list, name='corpus_list'),
    # Add more vector search URLs here later
    path('vector/search/', views.search_console, name='search_console'),
]
