# apis/viewsets.py
from rest_framework import viewsets, status, filters
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.utils import timezone
from django.db import transaction

# Core, Content, Integrations
from core.models import User, Role
from content.models import Category, Post
from integrations.health import get_system_health, get_connectors_health
from core.auth import RolePermission

# Vector Search
import logging
from vectorsearch.models import TextChunk, EmbeddingVersion, QueryLog
from vectorsearch.services import ingest, search as semantic_search
from vectorsearch.tasks import reembed_corpus_task
from vectorsearch.providers.utils import get_provider_instance

logger = logging.getLogger(__name__)

# Serializers and Filters
from .serializers import (
    UserSerializer, RoleSerializer, CategorySerializer, PostSerializer,
    DocumentIngestSerializer, VectorSearchRequestSerializer,
    ReembedRequestSerializer, SearchResultChunkSerializer
)
from .permissions import IsOwnerOrAdmin
from .filters import CategoryFilter, PostFilter
from alerts.models import Alert
from graph.models import TopicNode, TopicEdge
from graph.services.compute_ta_scores import calculate_ta_for_category
from calendar.models import ContentTask
from abtest.models import ABTest, TemplatePart

# Base ViewSets (User, Role, Content)
# ... (These remain largely the same as before) ...
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Add more granular permissions as needed

    def get_queryset(self):
        # Users can only see other users in their own organization.
        return User.objects.filter(organization=self.request.user.organization).order_by('-date_joined')

class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Roles are scoped to an organization.
        return Role.objects.filter(organization=self.request.user.organization)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_class = CategoryFilter
    search_fields = ['name', 'slug']

    def get_queryset(self):
        # Categories are scoped to a site, which belongs to an organization.
        return Category.objects.filter(site__organization=self.request.user.organization)

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filterset_class = PostFilter
    search_fields = ['title', 'content']

    def get_queryset(self):
        return Post.objects.filter(site__organization=self.request.user.organization)

    def perform_create(self, serializer):
        # When creating a post, automatically assign it to the user's site.
        # This assumes a simple one-site-per-user or default-site logic.
        user_site = Site.objects.filter(organization=self.request.user.organization).first()
        serializer.save(author=self.request.user, site=user_site)

# --- Vector Search ViewSet ---
class VectorSearchViewSet(viewsets.ViewSet):
    """
    API endpoints for the semantic search subsystem.
    Handles ingestion, searching, and management of vectorized documents.
    """
    permission_classes = [IsAuthenticated, RolePermission.of('admin', 'editor')]

    @action(detail=False, methods=['post'], serializer_class=DocumentIngestSerializer)
    def ingest(self, request: Request) -> Response:
        """Ingests a single document."""
        serializer = DocumentIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            document = ingest.ingest_document(**serializer.validated_data)
            return Response({'document_id': document.id, 'status': 'processing'}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], serializer_class=DocumentIngestSerializer(many=True))
    def ingest_bulk(self, request: Request) -> Response:
        """Ingests a batch of documents."""
        serializer = DocumentIngestSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        results = []
        with transaction.atomic(): # Ensure all or nothing for the initial DB write
            for doc_data in serializer.validated_data:
                try:
                    document = ingest.ingest_document(**doc_data)
                    results.append({'external_id': doc_data['external_id'], 'document_id': document.id, 'status': 'processing'})
                except Exception as e:
                    results.append({'external_id': doc_data['external_id'], 'error': str(e)})
        return Response(results, status=status.HTTP_207_MULTI_STATUS)

    @action(detail=False, methods=['post'], serializer_class=VectorSearchRequestSerializer)
    def search(self, request: Request) -> Response:
        """Performs a search query."""
        serializer = VectorSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        current_site = Site.objects.filter(organization=request.user.organization).first()
        if not current_site:
            return Response({'error': 'User has no associated site.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get the active embedding provider
            active_version = EmbeddingVersion.objects.filter(is_active=True).first()
            if not active_version:
                raise ValueError("No active embedding version configured.")
            provider = get_provider_instance(active_version)

            # Execute search
            results = semantic_search.execute_search(
                user=request.user,
                site=current_site,
                query_text=data['query'],
                embedding_provider=provider,
                mode=data['mode'],
                top_k=data['top_k'],
                alpha=data['alpha'],
                with_snippet=data['with_snippet'],
                corpus_ids=data.get('corpus_ids'),
                filters=data.get('filters')
            )
            # Serialize results
            result_serializer = SearchResultChunkSerializer(results, many=True)
            return Response(result_serializer.data)

        except Exception as e:
            logger.error(f"Search API error: {e}")
            return Response({'error': 'An error occurred during search.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], serializer_class=ReembedRequestSerializer)
    def reembed(self, request: Request) -> Response:
        """Triggers a re-embedding task for a corpus or specific documents."""
        serializer = ReembedRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get('corpus_id'):
            reembed_corpus_task.delay(str(data['corpus_id']), str(data['embedding_version_id']))
            message = f"Re-embedding queued for corpus {data['corpus_id']}."
        # Add logic for document_ids if needed
        else:
            return Response({'error': 'Either corpus_id or document_ids must be provided.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'queued', 'message': message}, status=status.HTTP_202_ACCEPTED)

# ... (Health and Vector Search ViewSets remain the same) ...

# --- Public Read-Only API for Frontend ---

class PublicPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only API endpoint for fetching published posts for the frontend.
    This endpoint is publicly accessible.
    """
    queryset = Post.objects.filter(status=Post.PostStatus.PUBLISHED).order_by('-published_at')
    serializer_class = PublicPostSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    # Add filtering for type, category, etc.
    filterset_fields = ['type', 'category__slug', 'tags__slug']


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request: Request, *args, **kwargs) -> Response:
        health_data = get_system_health()
        return Response(health_data)

class IntegrationsHealthCheckView(APIView):
    permission_classes = [IsAuthenticated, RolePermission.of('admin', 'editor')]
    def get(self, request: Request, *args, **kwargs) -> Response:
        connectors_data = get_connectors_health()
        return Response(connectors_data)

# --- Alerts API ---
class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type', 'severity', 'resolved_at']

    def get_queryset(self):
        # Users should only see alerts for sites in their organization.
        return Alert.objects.filter(site__organization=self.request.user.organization)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request: Request, pk: str = None) -> Response:
        alert = self.get_object()
        if not alert.acknowledged_by:
            alert.acknowledged_by = request.user
            alert.save()
        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request: Request, pk: str = None) -> Response:
        alert = self.get_object()
        if not alert.resolved_at:
            alert.resolved_at = timezone.now()
            alert.save()
        return Response(self.get_serializer(alert).data)

# --- Topic Graph API ---
class TopicNodeSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)
    class Meta:
        model = TopicNode
        fields = ['id', 'post_title', 'role', 'pagerank_internal', 'inlinks_count', 'outlinks_count']

class TopicEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicEdge
        fields = ['source', 'destination', 'anchor_text']

class TopicGraphViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TopicNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TopicNode.objects.filter(post__site__organization=self.request.user.organization)

    @action(detail=False, methods=['get'])
    def edges(self, request: Request) -> Response:
        queryset = TopicEdge.objects.filter(source__post__site__organization=request.user.organization)
        serializer = TopicEdgeSerializer(queryset, many=True)
        return Response(serializer.data)

# --- Topical Authority API ---
class TopicalAuthorityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        site = Site.objects.filter(organization=request.user.organization).first()
        if not site:
            return Response({"error": "No site associated with user's organization."}, status=status.HTTP_400_BAD_REQUEST)

        group_by = request.query_params.get('group', 'category')

        if group_by == 'category':
            categories = Category.objects.filter(site=site)
            results = [
                {'category': cat.name, 'ta_score': calculate_ta_for_category(cat)}
                for cat in categories
            ]
            return Response(results)
        else:
            return Response({"error": "Grouping by cluster is not yet implemented."}, status=status.HTTP_400_BAD_REQUEST)

# --- Calendar API ---
class ContentTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTask
        fields = '__all__'

class CalendarViewSet(viewsets.ModelViewSet):
    serializer_class = ContentTaskSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['state', 'assignee', 'type']

    def get_queryset(self):
        # Users should only see tasks for sites in their organization.
        return ContentTask.objects.filter(post__site__organization=self.request.user.organization)

    @action(detail=True, methods=['post'])
    def transition(self, request: Request, pk: str = None) -> Response:
        """Transitions a task to a new state."""
        task = self.get_object()
        new_state = request.data.get('state')
        if new_state in ContentTask.TaskState.values:
            task.state = new_state
            task.save()
            return Response(self.get_serializer(task).data)
        else:
            return Response({'error': 'Invalid state.'}, status=status.HTTP_400_BAD_REQUEST)

# --- A/B Testing API ---
class ABTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ABTest
        fields = '__all__'

class ABTestViewSet(viewsets.ModelViewSet):
    serializer_class = ABTestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ABTest.objects.filter(site__organization=self.request.user.organization)

    @action(detail=True, methods=['post'])
    def start(self, request: Request, pk: str = None) -> Response:
        test = self.get_object()
        if not test.started_at:
            test.started_at = timezone.now()
            test.stopped_at = None
            test.save()
        return Response(self.get_serializer(test).data)

    @action(detail=True, methods=['post'])
    def stop(self, request: Request, pk: str = None) -> Response:
        test = self.get_object()
        if not test.stopped_at:
            test.stopped_at = timezone.now()
            test.save()
        return Response(self.get_serializer(test).data)
