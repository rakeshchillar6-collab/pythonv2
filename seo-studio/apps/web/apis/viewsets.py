# apis/viewsets.py
from rest_framework import viewsets, status, filters
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.utils import timezone
from core.models import User, Role
from content.models import Category, Post
from .serializers import (
    UserSerializer, RoleSerializer, CategorySerializer, PostSerializer,
    TextChunkSerializer, VectorSearchRequestSerializer
)
from .permissions import IsOwnerOrAdmin
from .filters import CategoryFilter, PostFilter
from core.auth import RolePermission
from integrations.health import get_system_health, get_connectors_health
from vectorsearch.services import similarity_search
from vectorsearch.tasks import generate_embedding_for_chunk
from vectorsearch.models import TextChunk

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [RolePermission.of('admin')]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [RolePermission.of('admin')]
    lookup_field = 'slug'

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [RolePermission.of('admin', 'editor')]
    filterset_class = CategoryFilter
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'created_at']
    lookup_field = 'slug'

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrAdmin, RolePermission.of('admin', 'editor')]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['published_at', 'updated_at', 'title']
    lookup_field = 'slug'

    def get_queryset(self):
        user: User = self.request.user
        if user.is_authenticated and (user.has_role('admin', 'editor') or user.is_superuser):
            return Post.objects.all().prefetch_related('tags', 'category')
        return Post.objects.filter(status=Post.PostStatus.PUBLISHED).prefetch_related('tags', 'category')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[RolePermission.of('admin', 'editor')])
    def publish(self, request: Request, slug: str | None = None) -> Response:
        """
        Custom action to publish a draft post.
        """
        post = self.get_object()
        if post.status == Post.PostStatus.PUBLISHED:
            return Response({'detail': 'Post is already published.'}, status=status.HTTP_400_BAD_REQUEST)

        post.status = Post.PostStatus.PUBLISHED
        post.published_at = timezone.now()
        post.save()

        return Response(self.get_serializer(post).data)

# ... (Health and Vector Search ViewSets remain the same)
class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request: Request, *args, **kwargs) -> Response:
        health_data = get_system_health()
        overall_healthy = all(s["status"] == "ok" for s in health_data.values())
        http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(health_data, status=http_status)

class IntegrationsHealthCheckView(APIView):
    permission_classes = [RolePermission.of('admin', 'editor')]
    def get(self, request: Request, *args, **kwargs) -> Response:
        connectors_data = get_connectors_health()
        return Response(connectors_data)

class VectorSearchViewSet(viewsets.GenericViewSet):
    queryset = TextChunk.objects.all()
    permission_classes = [RolePermission.of('admin', 'editor')]
    @action(detail=False, methods=['post'], serializer_class=TextChunkSerializer)
    def ingest(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chunk = serializer.save()
        embedding = request.data.get('embedding')
        if embedding and isinstance(embedding, list) and len(embedding) == 1536:
            chunk.embedding = embedding
            chunk.save()
        else:
            generate_embedding_for_chunk.delay(str(chunk.id))
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], serializer_class=VectorSearchRequestSerializer)
    def search(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        results = similarity_search(vector=data['vector'], top_k=data['top_k'])
        result_serializer = TextChunkSerializer(results, many=True)
        return Response(result_serializer.data)
