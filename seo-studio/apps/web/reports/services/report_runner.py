# reports/services/report_runner.py
import csv
import logging
from io import StringIO
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db.models import Q

from ..models import ReportRun
from .dsl_parser import parse_dsl, DSLParserError, WHITELISTED_MODELS

logger = logging.getLogger(__name__)

def _build_orm_filters(parsed_dsl):
    """Builds a Django Q object from the parsed DSL filters."""
    q_objects = Q()

    operator_map = {
        '=': 'exact',
        '>': 'gt',
        '<': 'lt',
    }

    for f in parsed_dsl["filters"]:
        field = f["field"]
        op = operator_map.get(f["operator"])
        if not op:
            raise DSLParserError(f"Unsupported operator: {f['operator']}")

        lookup = f"{field}__{op}"
        q_objects &= Q(**{lookup: f["value"]})

    return q_objects


def run_report(run_id: str):
    """
    Executes a report run based on a saved DSL query.
    This involves parsing the DSL, building a safe ORM query, executing it,
    and saving the results to a CSV file.
    """
    try:
        report_run = ReportRun.objects.select_related('saved_report').get(id=run_id)
    except ReportRun.DoesNotExist:
        logger.error(f"ReportRun with id={run_id} not found.")
        return

    saved_report = report_run.saved_report
    report_run.status = ReportRun.RunStatus.RUNNING
    report_run.started_at = timezone.now()
    report_run.log = f"[{report_run.started_at}] - Starting report run...\n"
    report_run.save(update_fields=['status', 'started_at', 'log'])

    try:
        # 1. Parse the DSL query
        parsed_dsl = parse_dsl(saved_report.dsl_query)
        ModelClass = parsed_dsl["model_class"]

        report_run.log += f"[{timezone.now()}] - DSL parsed successfully. Querying model: {parsed_dsl['model_name']}.\n"
        report_run.save(update_fields=['log'])

        # 2. Build the ORM Query
        queryset = ModelClass.objects.filter(site=saved_report.site) # Base scope

        # Apply filters
        orm_filters = _build_orm_filters(parsed_dsl)
        queryset = queryset.filter(orm_filters)

        # Apply ordering
        if parsed_dsl["order_by"]:
            direction = "-" if parsed_dsl["order_by"]["direction"] == "DESC" else ""
            field = parsed_dsl["order_by"]["field"]
            queryset = queryset.order_by(f"{direction}{field}")

        # Apply limit
        if parsed_dsl["limit"]:
            queryset = queryset[:parsed_dsl["limit"]]

        # 3. Execute the query and generate CSV
        field_names = parsed_dsl["fields"]
        results = list(queryset.values(*field_names))

        report_run.log += f"[{timezone.now()}] - Query executed. Found {len(results)} records.\n"
        report_run.save(update_fields=['log'])

        string_io = StringIO()
        writer = csv.DictWriter(string_io, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(results)

        # 4. Save the CSV file to storage
        file_content = ContentFile(string_io.getvalue().encode('utf-8'))
        file_name = f"reports/{saved_report.id}/{report_run.id}.csv"
        report_run.result_file.save(file_name, file_content)

        # 5. Mark as complete
        report_run.status = ReportRun.RunStatus.COMPLETED
        report_run.log += f"[{timezone.now()}] - Report saved to {file_name}.\n"
        report_run.log += f"[{timezone.now()}] - Run completed successfully."

    except (DSLParserError, Exception) as e:
        logger.error(f"Report run {run_id} failed: {e}")
        report_run.status = ReportRun.RunStatus.FAILED
        report_run.log += f"[{timezone.now()}] - ERROR: {e}\n"
        report_run.log += f"[{timezone.now()}] - Run failed."

    finally:
        report_run.finished_at = timezone.now()
        report_run.save()
