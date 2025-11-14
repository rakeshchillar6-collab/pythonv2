# apis/urls/reports.py
from rest_framework.routers import DefaultRouter
from ..viewsets import ReportViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = router.urls
