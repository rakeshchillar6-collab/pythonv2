# apis/viewsets.py
from rest_framework import viewsets, permissions
from core.models import User
from content.models import Category, Post
from .serializers import UserSerializer, CategorySerializer, PostSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """
    queryset = Post.objects.filter(status=Post.PostStatus.PUBLISHED)
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        # Admin users can see all posts, others only see published posts
        if self.request.user.is_staff:
            return Post.objects.all()
        return Post.objects.filter(status=Post.PostStatus.PUBLISHED)

    def perform_create(self, serializer):
        # Automatically set the author to the current user
        serializer.save(author=self.request.user)
