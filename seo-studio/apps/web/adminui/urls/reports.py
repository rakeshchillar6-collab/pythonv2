# adminui/urls/reports.py
from django.urls import path
from ..views import reports as report_views

urlpatterns = [
    path('', report_views.report_dashboard_view, name='reports-dashboard'),
    path('list/', report_views.report_list_view, name='reports-list'),
    path('runs/', report_views.report_runs_list_view, name='reports-runs-list'),
    path('create/', report_views.report_create_edit_view, name='reports-create'),
    path('<uuid:report_id>/edit/', report_views.report_create_edit_view, name='reports-edit'),
    path('<uuid:report_id>/run/', report_views.report_trigger_run_view, name='reports-run'),
]
