# apis/urls/metaphorge_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..viewsets.metaphorge_viewsets import MFProjectViewSet

router = DefaultRouter()
router.register(r'metaphorge/projects', MFProjectViewSet, basename='mf-project')

urlpatterns = [
    path('', include(router.urls)),
]
