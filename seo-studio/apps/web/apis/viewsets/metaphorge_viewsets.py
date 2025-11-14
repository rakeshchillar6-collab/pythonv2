# apis/viewsets/metaphorge_viewsets.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Site
from metaphorge.models import MFProject, MFSeed, MFCluster, MFLSIEntity, MFDraft
from ..serializers.metaphorge_serializers import *
from metaphorge.tasks import orchestrator

class MFProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Metaphorge Projects.
    """
    queryset = MFProject.objects.all()
    serializer_class = MFProjectSerializer

    def get_queryset(self):
        site = Site.objects.filter(organization=self.request.user.organization).first()
        return self.queryset.filter(site=site)

    def get_serializer_class(self):
        if self.action == 'list':
            return MFProjectListSerializer
        return MFProjectSerializer

    def perform_create(self, serializer):
        site = Site.objects.filter(organization=self.request.user.organization).first()
        serializer.save(site=site, created_by=self.request.user)

    # --- Pipeline Control Actions ---
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        orchestrator.start_project(pk)
        return Response({'status': 'Project execution started.'})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        orchestrator.pause_project(pk)
        return Response({'status': 'Project execution paused.'})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        orchestrator.resume_project(pk)
        return Response({'status': 'Project execution resumed.'})

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        orchestrator.stop_project(pk)
        return Response({'status': 'Project execution stopped.'})

    # --- Data Retrieval Actions ---
    @action(detail=True, methods=['get'])
    def clusters(self, request, pk=None):
        project = self.get_object()
        clusters = MFCluster.objects.filter(project=project)
        serializer = MFClusterSerializer(clusters, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lsi_entities(self, request, pk=None):
        project = self.get_object()
        # This assumes one lsi_entity object per project for simplicity
        lsi_entities = MFLSIEntity.objects.filter(project=project)
        serializer = MFLSIEntitySerializer(lsi_entities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def seeds(self, request, pk=None):
        project = self.get_object()
        serializer = MFSeedSerializer(data=request.data, many=True)
        if serializer.is_valid():
            seeds = [MFSeed(project=project, **item) for item in serializer.validated_data]
            MFSeed.objects.bulk_create(seeds)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
