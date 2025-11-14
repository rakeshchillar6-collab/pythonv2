# apis/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .viewsets import (
    UserViewSet, RoleViewSet, CategoryViewSet, PostViewSet, PublicPostViewSet,
    HealthCheckView, IntegrationsHealthCheckView, VectorSearchViewSet, AlertViewSet,
    TopicGraphViewSet, CalendarViewSet, ABTestViewSet, TopicalAuthorityView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'posts', PostViewSet, basename='post') # Internal CRUD
router.register(r'public/posts', PublicPostViewSet, basename='public-post') # Public API
router.register(r'vector', VectorSearchViewSet, basename='vector')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'graph/nodes', TopicGraphViewSet, basename='topic-node')
router.register(r'calendar/tasks', CalendarViewSet, basename='calendar-task')
router.register(r'abtests', ABTestViewSet, basename='abtest')

app_name = 'apis'

urlpatterns = [
    path('', include(router.urls)),
    path('', include('apis.urls.reports')),

    # SEO & Analytics Endpoints
    path('seo/ta/', TopicalAuthorityView.as_view(), name='topical-authority'),

    # Health check endpoints
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('integrations/health/', IntegrationsHealthCheckView.as_view(), name='integrations-health-check'),

    # JWT Authentication endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
