# reports/services/runner.py
import csv
import logging
from io import StringIO
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from ..models import SavedReport, ReportRun
from .dsl_parser import parse_dsl_query, build_orm_query, DSLParserError

logger = logging.getLogger(__name__)

def run_saved_report(report_id: str):
    """
    Executes a saved analytical report.
    """
    try:
        report = SavedReport.objects.get(id=report_id)
    except SavedReport.DoesNotExist:
        logger.error(f"SavedReport with id={report_id} not found.")
        return

    run = ReportRun.objects.create(report=report, status=ReportRun.Status.RUNNING)
    report.last_run_at = run.started_at
    report.save(update_fields=['last_run_at'])

    try:
        # 1. Parse and validate the DSL
        parsed_query = parse_dsl_query(report.query_dsl)

        # 2. Build and execute the ORM query
        queryset = build_orm_query(parsed_query)
        results = list(queryset)

        run.rows = len(results)

        # 3. Generate CSV output
        if results:
            field_names = results[0].keys()
            string_io = StringIO()
            writer = csv.DictWriter(string_io, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(results)

            # 4. Save to storage
            file_content = ContentFile(string_io.getvalue().encode('utf-8'))
            file_name = f"reports/{report.id}/{run.id}.csv"

            # Use default_storage to save the file
            saved_path = default_storage.save(file_name, file_content)
            run.sample_url = default_storage.url(saved_path)

        run.status = ReportRun.Status.SUCCESS
        report.last_status = ReportRun.Status.SUCCESS

    except (DSLParserError, Exception) as e:
        logger.error(f"Report run {run.id} for report {report.id} failed: {e}")
        run.status = ReportRun.Status.FAILED
        run.error = str(e)
        report.last_status = ReportRun.Status.FAILED

    finally:
        run.finished_at = timezone.now()
        run.save()
        report.save(update_fields=['last_status'])
