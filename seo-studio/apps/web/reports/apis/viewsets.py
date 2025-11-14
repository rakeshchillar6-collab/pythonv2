# reports/apis/viewsets.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import SavedReport, ReportRun
from .serializers import SavedReportSerializer, ReportRunSerializer
from ..tasks import run_report_task

class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing Saved Reports and triggering Report Runs.
    """
    queryset = SavedReport.objects.all()
    serializer_class = SavedReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter reports by the current user's organization
        return self.queryset.filter(site__organization=self.request.user.organization)

    @action(detail=True, methods=['post'], url_path='run')
    def run_report(self, request, pk=None):
        """
        Triggers an asynchronous run of a saved report.
        """
        saved_report = self.get_object()

        # Create a new ReportRun instance
        report_run = ReportRun.objects.create(
            saved_report=saved_report,
            triggered_by=request.user,
            status=ReportRun.RunStatus.PENDING
        )

        # Launch the Celery task
        run_report_task.delay(str(report_run.id))

        serializer = ReportRunSerializer(report_run)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], url_path='runs')
    def list_runs(self, request):
        """
        Lists all historical and current runs for reports in the organization.
        """
        saved_report_ids = self.get_queryset().values_list('id', flat=True)
        runs = ReportRun.objects.filter(saved_report_id__in=saved_report_ids).order_by('-created_at')

        page = self.paginate_queryset(runs)
        if page is not None:
            serializer = ReportRunSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReportRunSerializer(runs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='runs/(?P<run_id>[^/.]+)')
    def retrieve_run(self, request, pk=None, run_id=None):
        """
        Retrieves a specific report run, including a download link if completed.
        """
        try:
            run = ReportRun.objects.get(id=run_id, saved_report_id=pk)
            serializer = ReportRunSerializer(run)
            return Response(serializer.data)
        except ReportRun.DoesNotExist:
            return Response({'error': 'Report run not found.'}, status=status.HTTP_404_NOT_FOUND)
