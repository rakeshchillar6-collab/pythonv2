# apis/viewsets/seo_viewsets.py
from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from core.models import Site
from content.models import Post
from ..serializers.seo_serializers import *

# Services
from schema_builder.services.renderer import render_schema_for_post
from sitemap.services.generator import generate_sitemap_for_site
from robots.services.calculator import get_effective_robots_for_url, get_robots_txt_for_site
from publishing.tasks import enqueue_publish_job

# --- Base ViewSet for Site-scoped resources ---
class SiteScopedViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Automatically filter queryset by the user's site.
        site = Site.objects.filter(organization=self.request.user.organization).first()
        return self.queryset.filter(site=site)

    def perform_create(self, serializer):
        site = Site.objects.filter(organization=self.request.user.organization).first()
        serializer.save(site=site)

# --- Schema Builder ---
class SchemaTemplateViewSet(SiteScopedViewSet):
    queryset = SchemaTemplate.objects.all()
    serializer_class = SchemaTemplateSerializer

class SchemaAssignmentViewSet(SiteScopedViewSet):
    queryset = SchemaAssignment.objects.all()
    serializer_class = SchemaAssignmentSerializer

class SchemaRenderView(APIView):
    def get(self, request: Request) -> Response:
        post_id = request.query_params.get('post_id')
        if not post_id:
            return Response({"error": "post_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Security check: ensure post belongs to user's org
        if not Post.objects.filter(id=post_id, site__organization=request.user.organization).exists():
             return Response({"error": "Post not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        jsonld = render_schema_for_post(post_id)
        return Response(jsonld)

# --- Sitemap ---
class SitemapRuleViewSet(SiteScopedViewSet):
    queryset = SitemapRule.objects.all()
    serializer_class = SitemapRuleSerializer

class SitemapBuildViewSet(viewsets.ViewSet):
    def list(self, request: Request) -> Response:
        site = Site.objects.filter(organization=request.user.organization).first()
        logs = SitemapBuildLog.objects.filter(site=site).order_by('-created_at')
        serializer = SitemapBuildLogSerializer(logs, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        site = Site.objects.filter(organization=request.user.organization).first()
        generate_sitemap_for_site.delay(str(site.id))
        return Response({"status": "Sitemap generation queued."}, status=status.HTTP_202_ACCEPTED)

# --- Robots ---
class RobotsGlobalViewSet(viewsets.ModelViewSet):
    serializer_class = RobotsGlobalSerializer
    def get_queryset(self):
        site = Site.objects.filter(organization=self.request.user.organization).first()
        return RobotsGlobal.objects.filter(site=site)

class RobotsRuleViewSet(SiteScopedViewSet):
    queryset = RobotsRule.objects.all()
    serializer_class = RobotsRuleSerializer

class EffectiveRobotsView(APIView):
    def get(self, request: Request) -> Response:
        url = request.query_params.get('url')
        if not url:
            return Response({"error": "url parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        site = Site.objects.filter(organization=request.user.organization).first()
        effective_rules = get_effective_robots_for_url(str(site.id), url)
        return Response(effective_rules)

# --- Publishing ---
class PublishDestinationViewSet(SiteScopedViewSet):
    queryset = PublishDestination.objects.all()
    serializer_class = PublishDestinationSerializer

    @action(detail=False, methods=['post'], serializer_class=HeadlessConnectionTestSerializer)
    def test_connection(self, request: Request) -> Response:
        # This is a placeholder for a real connection test
        # In a real app, you would try to send a PING request or similar
        return Response({"status": "ok", "message": "Connection parameters seem valid."})

class PublishJobViewSet(viewsets.ModelViewSet):
    serializer_class = PublishJobSerializer

    def get_queryset(self):
        return PublishJob.objects.filter(destination__site__organization=self.request.user.organization)

    def create(self, request: Request, *args, **kwargs):
        serializer = PublishJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = enqueue_publish_job(**serializer.validated_data)
        if job:
            return Response(PublishJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)
        return Response({"message": "Duplicate job skipped."}, status=status.HTTP_200_OK)

# --- Content Render Cache View ---
class ContentRenderCacheView(APIView):
    """
    Publicly accessible endpoint to fetch pre-rendered content for a post.
    Used by the Next.js frontend when using the 'local' publisher.
    """
    permission_classes = [] # Allow anonymous access

    def get(self, request: Request, slug: str) -> Response:
        from publishing.models import ContentRenderCache
        try:
            cache_entry = ContentRenderCache.objects.select_related('post').get(post__slug=slug, post__status=Post.PostStatus.PUBLISHED)

            response_data = {
                "id": cache_entry.post.id,
                "slug": cache_entry.post.slug,
                "html": cache_entry.rendered_html,
                "meta": cache_entry.rendered_meta,
                "jsonld": cache_entry.rendered_jsonld,
                "updated_at": cache_entry.updated_at,
                "content_version_hash": cache_entry.content_version_hash,
            }
            return Response(response_data)

        except ContentRenderCache.DoesNotExist:
            return Response({"error": "Content not found or not published."}, status=status.HTTP_404_NOT_FOUND)
