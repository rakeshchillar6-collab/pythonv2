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
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<uuid:pk>/update/', views.category_update, name='category_update'),
    path('categories/<uuid:pk>/delete/', views.category_delete, name='category_delete'),
]
