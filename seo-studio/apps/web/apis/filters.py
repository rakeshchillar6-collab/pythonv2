# apis/filters.py
from django_filters import rest_framework as filters
from content.models import Post, Category

class CategoryFilter(filters.FilterSet):
    """FilterSet for the Category model."""
    class Meta:
        model = Category
        fields = {
            'name': ['icontains'],
            'slug': ['exact'],
        }

class PostFilter(filters.FilterSet):
    """FilterSet for the Post model."""
    class Meta:
        model = Post
        fields = {
            'title': ['icontains'],
            'status': ['exact'],
            'category__slug': ['exact'],
            'tags__slug': ['in'],
        }
