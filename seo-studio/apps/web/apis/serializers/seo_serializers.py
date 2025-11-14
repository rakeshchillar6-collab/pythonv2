# apis/serializers/seo_serializers.py
from rest_framework import serializers

from schema_builder.models import SchemaTemplate, SchemaAssignment
from sitemap.models import SitemapRule, HreflangMap, SitemapBuildLog
from robots.models import RobotsGlobal, RobotsRule, MetaRobotsOverride
from publishing.models import PublishDestination, PublishJob, PublishMap
from publishing.connectors.headless import HeadlessPublisher # For testing connection

# --- Schema Builder Serializers ---
class SchemaTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaTemplate
        fields = '__all__'
        read_only_fields = ['site']

class SchemaAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaAssignment
        fields = '__all__'
        read_only_fields = ['site']

# --- Sitemap Serializers ---
class SitemapRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SitemapRule
        fields = '__all__'
        read_only_fields = ['site']

class SitemapBuildLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SitemapBuildLog
        fields = '__all__'

# --- Robots Serializers ---
class RobotsGlobalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotsGlobal
        fields = ['id', 'content', 'updated_at']

class RobotsRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotsRule
        fields = '__all__'
        read_only_fields = ['site']

# --- Publishing Serializers ---
class PublishDestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishDestination
        fields = '__all__'
        read_only_fields = ['site']

class PublishJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishJob
        fields = '__all__'

class PublishJobCreateSerializer(serializers.Serializer):
    post_id = serializers.UUIDField()
    destination_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=PublishJob.Action.choices)
    scheduled_at = serializers.DateTimeField(required=False)

class HeadlessConnectionTestSerializer(serializers.Serializer):
    endpoint_url = serializers.URLField()
    auth_header_template = serializers.CharField(allow_blank=True)
    api_key = serializers.CharField(allow_blank=True)
    headers = serializers.JSONField(default=dict)
