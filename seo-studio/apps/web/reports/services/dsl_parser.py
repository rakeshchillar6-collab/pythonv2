# reports/services/dsl_parser.py
import re
from datetime import date, timedelta
from django.utils import timezone
from content.models import Post, Category
from seo_trends.models import RankTimeSeries

# --- Whitelist Configuration ---
# This is a critical security boundary. Only expose models and fields that are
# safe and intended for reporting.
WHITELISTED_MODELS = {
    "posts": {
        "model": Post,
        "fields": {"id", "title", "slug", "status", "published_at", "created_at", "updated_at"},
    },
    "categories": {
        "model": Category,
        "fields": {"id", "name", "slug"},
    },
    "performance": {
        "model": RankTimeSeries,
        "fields": {"date", "page", "clicks", "impressions", "ctr", "position"},
    }
}

class DSLParserError(ValueError):
    """Custom exception for DSL parsing errors."""
    pass

def _parse_relative_date(value_str):
    """Parses relative date strings like "30d"."""
    match = re.match(r'^"(\d+)d"$', value_str)
    if match:
        days_ago = int(match.group(1))
        return (timezone.now() - timedelta(days=days_ago)).date()
    # Fallback for simple quoted strings that might look like dates
    return value_str[1:-1]

def _parse_value(value_str):
    """Parses a value string, handling strings, numbers, and relative dates."""
    value_str = value_str.strip()
    if value_str.startswith('"') and value_str.endswith('"'):
        # Check for relative date first
        if re.match(r'^"\d+d"$', value_str):
            return _parse_relative_date(value_str)
        return value_str[1:-1] # It's a regular string
    if value_str.isdigit():
        return int(value_str)
    try:
        return float(value_str)
    except ValueError:
        raise DSLParserError(f"Unsupported value type: {value_str}")

def parse_dsl(query: str):
    """
    Parses a simplified, secure DSL for generating database reports.
    """
    query = query.strip()

    # Regex to capture the main parts of the query
    main_pattern = re.compile(
        r'^FROM\s+(?P<model>\w+)\s+'
        r'SELECT\s+(?P<fields>[\w\s,]+)\s*'
        r'(?:WHERE\s+(?P<where>.*?))?\s*'
        r'(?:ORDER\s+BY\s+(?P<orderby>\w+\s+(?:ASC|DESC)))?\s*'
        r'(?:LIMIT\s+(?P<limit>\d+))?$',
        re.IGNORECASE
    )

    match = main_pattern.match(query)
    if not match:
        raise DSLParserError("Invalid query structure. Must be FROM... SELECT... [WHERE...] [ORDER BY...] [LIMIT...]")

    parts = match.groupdict()
    model_name = parts.get('model').lower()

    # --- Validation Step 1: Model Whitelisting ---
    if model_name not in WHITELISTED_MODELS:
        raise DSLParserError(f"Invalid model '{model_name}' specified. Allowed models are: {', '.join(WHITELISTED_MODELS.keys())}")

    model_config = WHITELISTED_MODELS[model_name]
    allowed_fields = model_config["fields"]

    # --- Parse and Validate Fields ---
    fields_str = parts.get('fields', '').strip()
    if not fields_str:
        raise DSLParserError("SELECT statement cannot be empty.")

    selected_fields = [f.strip() for f in fields_str.split(',')]
    for field in selected_fields:
        if field not in allowed_fields:
            raise DSLParserError(f"Invalid field '{field}' for model '{model_name}'. Allowed fields are: {', '.join(allowed_fields)}")

    # --- Parse and Validate WHERE clause ---
    filters = []
    where_clause = parts.get('where')
    if where_clause:
        conditions = re.split(r'\s+AND\s+', where_clause.strip(), flags=re.IGNORECASE)
        for cond in conditions:
            cond_match = re.match(r'(\w+)\s*([<>=])\s*(.*)', cond.strip())
            if not cond_match:
                raise DSLParserError(f"Malformed WHERE condition: '{cond}'")

            field, op, value_str = cond_match.groups()

            if field not in allowed_fields:
                raise DSLParserError(f"Invalid filter field '{field}' for model '{model_name}'.")

            value = _parse_value(value_str)
            filters.append({"field": field, "operator": op, "value": value})

    # --- Parse and Validate ORDER BY clause ---
    order_by = None
    orderby_clause = parts.get('orderby')
    if orderby_clause:
        field, direction = orderby_clause.split()
        if field not in allowed_fields:
            raise DSLParserError(f"Invalid ORDER BY field '{field}' for model '{model_name}'.")
        order_by = {"field": field, "direction": direction.upper()}

    # --- Parse and Validate LIMIT clause ---
    limit = None
    limit_clause = parts.get('limit')
    if limit_clause:
        limit = int(limit_clause)

    return {
        "model_name": model_name,
        "model_class": model_config["model"],
        "fields": selected_fields,
        "filters": filters,
        "order_by": order_by,
        "limit": limit,
    }
