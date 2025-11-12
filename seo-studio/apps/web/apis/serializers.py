# apis/serializers.py
from rest_framework import serializers
from core.models import User, Role
from content.models import Category, Post

class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model."""
    class Meta:
        model = Role
        fields = ['id', 'name', 'slug']

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model, including roles."""
    roles = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Role.objects.all()
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'roles']
        read_only_fields = ['is_staff']

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent']

class PostSerializer(serializers.ModelSerializer):
    """Serializer for the Post model."""
    author = serializers.ReadOnlyField(source='author.email')
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug', required=False
    )

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'status',
            'published_at', 'author', 'category', 'tags'
        ]
        read_only_fields = ['id', 'author']

# --- Vector Search Serializers ---
from vectorsearch.models import TextChunk

class TextChunkSerializer(serializers.ModelSerializer):
    """Serializer for the TextChunk model."""
    class Meta:
        model = TextChunk
        fields = ['id', 'title', 'body', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']

class VectorSearchRequestSerializer(serializers.Serializer):
    """Serializer for validating vector search requests."""
    vector = serializers.ListField(
        child=serializers.FloatField(),
        required=True,
        min_length=1536,
        max_length=1536
    )
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=100)
    # Add filters field if needed in the future

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return validated_data
