# apis/serializers/metaphorge_serializers.py
from rest_framework import serializers
from metaphorge.models import MFProject, MFSeed, MFCluster, MFLSIEntity, MFDraft

class MFProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFProject
        fields = '__all__'
        read_only_fields = ['site', 'created_by']

class MFProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFProject
        fields = ['id', 'name', 'status', 'stage', 'created_at']

class MFSeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFSeed
        fields = ['text', 'lang', 'source']

class MFClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFCluster
        fields = ['id', 'main_key', 'secondaries', 'phrases', 'similarity_k']

class MFLSIEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MFLSIEntity
        fields = ['lsi', 'entities']

class MFDraftSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = MFDraft
        fields = ['id', 'post', 'post_title', 'status']
