# adminui/urls/schema_builder_urls.py
from django.urls import path
from ..views.schema_builder import templates as template_views
from ..views.schema_builder import assignments as assignment_views

urlpatterns = [
    # Schema Template Management
    path('templates/', template_views.template_dashboard, name='schema-template-dashboard'),
    path('templates/list/', template_views.template_list_partial, name='schema-template-list-partial'),
    path('templates/create/', template_views.template_create_edit, name='schema-template-create'),
    path('templates/<uuid:template_id>/edit/', template_views.template_create_edit, name='schema-template-edit'),
    path('templates/<uuid:template_id>/delete/', template_views.template_delete, name='schema-template-delete'),

    # Schema Assignment Management
    path('assignments/', assignment_views.assignment_dashboard, name='schema-assignment-dashboard'),
    path('assignments/create/', assignment_views.assignment_create, name='schema-assignment-create'),
    path('assignments/<uuid:assignment_id>/delete/', assignment_views.assignment_delete, name='schema-assignment-delete'),
]
