# apis/serializers.py
from rest_framework import serializers
from core.models import User
from content.models import Category, Post

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['is_staff']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent']

class PostSerializer(serializers.ModelSerializer):
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
