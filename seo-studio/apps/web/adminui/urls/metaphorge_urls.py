# adminui/urls/metaphorge_urls.py
from django.urls import path
from ..views.metaphorge import projects as project_views

urlpatterns = [
    # Project Dashboard & Control
    path('projects/', project_views.project_dashboard, name='mf-project-dashboard'),
    path('projects/list/', project_views.project_list_partial, name='mf-project-list-partial'),
    path('projects/create/', project_views.project_create, name='mf-project-create'),
    path('projects/create/modal/', project_views.project_create_modal, name='mf-project-create-modal'),

    # Project Actions
    path('projects/<uuid:project_id>/start/', project_views.project_start, name='mf-project-start'),
    path('projects/<uuid:project_id>/pause/', project_views.project_pause, name='mf-project-pause'),
    path('projects/<uuid:project_id>/resume/', project_views.project_resume, name='mf-project-resume'),
]
