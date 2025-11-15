# adminui/urls/ops_urls.py
from django.urls import path
from ..views.ops import health as health_views
from ..views.ops import compliance as compliance_views

urlpatterns = [
    path('health/', health_views.system_health_dashboard, name='ops-health'),
    path('compliance/', compliance_views.compliance_dashboard, name='ops-compliance'),
]
