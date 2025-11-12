# apis/serializers.py
from rest_framework import serializers
from core.models import User, Role
from content.models import Category, Post
from vectorsearch.models import Corpus, Document, TextChunk

# --- Auth & Core Serializers ---
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'slug']

class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(many=True, slug_field='slug', queryset=Role.objects.all())
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'roles']
        read_only_fields = ['is_staff']

# --- Content Serializers ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent']

class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.email')
    category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='slug', required=False)
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'content', 'excerpt', 'status', 'published_at', 'author', 'category', 'tags']
        read_only_fields = ['id', 'author']

# --- Vector Search Serializers ---

# Input Serializers for API Validation
class DocumentIngestSerializer(serializers.Serializer):
    corpus_id = serializers.UUIDField()
    external_id = serializers.CharField(max_length=255)
    title = serializers.CharField(max_length=512)
    raw_text = serializers.CharField()
    metadata = serializers.JSONField(default=dict)

class SearchFilterSerializer(serializers.Serializer):
    content_type = serializers.ChoiceField(choices=Corpus.ContentType.choices, required=False)
    lang = serializers.ChoiceField(choices=Corpus.Language.choices, required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)

class VectorSearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    mode = serializers.ChoiceField(choices=QueryLog.SearchMode.choices, default=QueryLog.SearchMode.HYBRID)
    corpus_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    filters = SearchFilterSerializer(required=False)
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=50)
    alpha = serializers.FloatField(default=0.5, min_value=0.0, max_value=1.0)
    with_snippet = serializers.BooleanField(default=True)
    with_metadata = serializers.BooleanField(default=True)

class ReembedRequestSerializer(serializers.Serializer):
    corpus_id = serializers.UUIDField(required=False)
    document_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    embedding_version_id = serializers.UUIDField(required=True)

# Output Serializers for Search Results
class SearchResultChunkSerializer(serializers.ModelSerializer):
    score = serializers.FloatField(read_only=True)
    snippet = serializers.CharField(read_only=True)
    document_id = serializers.UUIDField(source='document.id')
    document_title = serializers.CharField(source='document.title')
    document_metadata = serializers.JSONField(source='document.metadata')

    class Meta:
        model = TextChunk
        fields = ['document_id', 'document_title', 'id', 'score', 'snippet', 'document_metadata']

# --- Public API Serializers (for Next.js) ---

class PublicPostSerializer(serializers.ModelSerializer):
    """A read-only serializer for public post data."""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'body_html', 'summary',
            'seo_title', 'seo_description', 'published_at',
            'read_time_min', 'author_name', 'category_name', 'tags'
        ]
