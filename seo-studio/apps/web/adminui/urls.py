# adminui/urls.py
from django.urls import path
from . import views

app_name = 'adminui'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('health-check/', views.health_check, name='health_check'),

    # Category CRUD URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<uuid:pk>/update/', views.category_update, name='category_update'),
    path('categories/<uuid:pk>/delete/', views.category_delete, name='category_delete'),
]
