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

# Base ViewSets (User, Role, Content)
# ... (These remain largely the same as before) ...
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, RolePermission.of('admin')]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, RolePermission.of('admin')]
    lookup_field = 'slug'

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, RolePermission.of('admin', 'editor')]
    filterset_class = CategoryFilter
    search_fields = ['name', 'slug']
    lookup_field = 'slug'

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filterset_class = PostFilter
    search_fields = ['title', 'content']
    lookup_field = 'slug'
    # ... (get_queryset, perform_create, publish action)

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

        # Site/Corpus filtering based on user permissions
        # TODO: Implement RBAC to filter corpus_ids based on request.user.site

        try:
            # Get the active embedding provider
            active_version = EmbeddingVersion.objects.filter(is_active=True).first()
            if not active_version:
                raise ValueError("No active embedding version configured.")
            provider = get_provider_instance(active_version)

            # Execute search
            # TODO: Determine the site based on user profile or request context
            current_site = None
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

# Health Check Views (remain the same)
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
