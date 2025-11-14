# apis/urls/seo_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..viewsets.seo_viewsets import (
    SchemaTemplateViewSet, SchemaAssignmentViewSet, SchemaRenderView,
    SitemapRuleViewSet, SitemapBuildViewSet,
    RobotsGlobalViewSet, RobotsRuleViewSet, EffectiveRobotsView,
    PublishDestinationViewSet, PublishJobViewSet
)

router = DefaultRouter()
router.register(r'schema/templates', SchemaTemplateViewSet, basename='schema-template')
router.register(r'schema/assignments', SchemaAssignmentViewSet, basename='schema-assignment')
router.register(r'sitemap/rules', SitemapRuleViewSet, basename='sitemap-rule')
router.register(r'sitemap/build', SitemapBuildViewSet, basename='sitemap-build')
router.register(r'robots/global', RobotsGlobalViewSet, basename='robots-global')
router.register(r'robots/rules', RobotsRuleViewSet, basename='robots-rule')
router.register(r'publish/destinations', PublishDestinationViewSet, basename='publish-destination')
router.register(r'publish/jobs', PublishJobViewSet, basename='publish-job')

urlpatterns = [
    path('', include(router.urls)),
    path('schema/render/', SchemaRenderView.as_view(), name='schema-render'),
    path('robots/effective/', EffectiveRobotsView.as_view(), name='robots-effective'),
]
