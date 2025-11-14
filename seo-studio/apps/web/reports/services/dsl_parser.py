# reports/services/dsl_parser.py
import re
from datetime import timedelta
from django.utils import timezone
from django.db import models

# Import all models that can be queried
from content.models import Post, Category
from rankme.models import RankMeScore
from graph.models import TopicNode
from rss.models import FeedItem
from autolink.models import LinkCandidate

# --- Whitelist Configuration ---
# This is the security boundary for the report builder.
WHITELIST = {
    "posts": {
        "model": Post,
        "fields": {"id", "title", "status", "published_at", "updated_at", "post_type"},
        "joins": {
            "category": "category",
            "rankme": "rankme_score",
        }
    },
    "categories": {
        "model": Category,
        "fields": {"id", "name", "slug"},
    },
    "rankme": {
        "model": RankMeScore,
        "fields": {"score", "seo_score", "content_score"},
    },
    # Add other models like links, rum, gsc, rss, metaphorge here
}

class DSLParserError(ValueError):
    pass

def parse_dsl_query(dsl: dict) -> dict:
    """
    Parses and validates a structured DSL query dictionary.
    """
    from_model_name = dsl.get("from")
    if not from_model_name or from_model_name not in WHITELIST:
        raise DSLParserError(f"Invalid 'from' model: {from_model_name}")

    model_config = WHITELIST[from_model_name]
    ModelClass = model_config["model"]
    allowed_fields = set(model_config["fields"])
    allowed_joins = model_config.get("joins", {})

    # --- Select ---
    select_fields = dsl.get("select", ["id"])
    for field in select_fields:
        if isinstance(field, str):
            if field not in allowed_fields:
                raise DSLParserError(f"Field '{field}' is not allowed for model '{from_model_name}'")
        # TODO: Add validation for aggregation dicts like {"func": "count", "field": "id"}

    # --- Joins ---
    joins = dsl.get("join", [])
    related_fields = []
    for join_alias in joins:
        if join_alias not in allowed_joins:
            raise DSLParserError(f"Join '{join_alias}' is not allowed for model '{from_model_name}'")
        related_fields.append(allowed_joins[join_alias])

    # --- Where ---
    where_clauses = dsl.get("where", [])
    # TODO: Implement a robust WHERE clause validator

    # --- Group By, Order By, Limit ---
    # TODO: Implement validators for these clauses

    return {
        "model": ModelClass,
        "select_fields": select_fields,
        "related_fields": related_fields,
        "where_clauses": where_clauses,
        # ... other parsed parts
    }


def build_orm_query(parsed_query: dict):
    """
    Builds a Django ORM queryset from a parsed and validated DSL query.
    """
    ModelClass = parsed_query["model"]
    queryset = ModelClass.objects.all()

    # Apply joins
    if parsed_query["related_fields"]:
        queryset = queryset.select_related(*parsed_query["related_fields"])

    # Apply filters (simplified for now)
    q_objects = models.Q()
    for clause in parsed_query["where_clauses"]:
        # In a real implementation, this would be a secure lookup builder
        q_objects &= models.Q(**{clause["field"]: clause["value"]})
    queryset = queryset.filter(q_objects)

    # Apply select/values
    # This is a simplified values() call. Aggregations would need .annotate()
    queryset = queryset.values(*parsed_query["select_fields"])

    return queryset
