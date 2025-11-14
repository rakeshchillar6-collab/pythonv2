# adminui/urls/publishing_urls.py
from django.urls import path
from ..views.publishing import destinations as destination_views
from ..views.publishing import jobs as job_views

urlpatterns = [
    # Publish Destination Management
    path('destinations/', destination_views.destination_dashboard, name='destination-dashboard'),
    path('destinations/create/', destination_views.destination_create, name='destination-create'),
    path('destinations/<uuid:dest_id>/delete/', destination_views.destination_delete, name='destination-delete'),

    # Publish Job Management
    path('jobs/', job_views.job_dashboard, name='job-dashboard'),
    path('jobs/list/', job_views.job_list_partial, name='job-list-partial'),
    path('jobs/<uuid:job_id>/', job_views.job_detail_modal, name='job-detail'),
    path('jobs/<uuid:job_id>/retry/', job_views.job_retry, name='job-retry'),
]
