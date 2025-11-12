# integrations/health.py
import time
from typing import TypedDict
from django.db import connection, DatabaseError
from django.conf import settings
from redis import Redis
from celery.app.control import Control
from celery.result import AsyncResult
from seo_studio.celery import app as celery_app
from .models import Connector

class HealthStatus(TypedDict):
    """A dictionary representing the health status of a service."""
    status: str
    details: str

def check_postgres() -> HealthStatus:
    """Checks the status of the PostgreSQL database."""
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok", "details": "Database connection is healthy."}
    except DatabaseError as e:
        return {"status": "error", "details": f"Database connection error: {e}"}

def check_redis() -> HealthStatus:
    """Checks the status of the Redis server."""
    try:
        redis_client: Redis = Redis.from_url(settings.REDIS_URL)
        if redis_client.ping():
            return {"status": "ok", "details": "Redis connection is healthy."}
        else:
            return {"status": "error", "details": "Redis server did not respond to PING."}
    except Exception as e:
        return {"status": "error", "details": f"Redis connection error: {e}"}

def check_celery_workers() -> HealthStatus:
    """Checks for active Celery workers."""
    try:
        control: Control = celery_app.control
        workers = control.ping(timeout=1.0)
        if not workers:
            return {"status": "error", "details": "No active Celery workers found."}

        # Optionally, check worker stats
        stats = control.inspect().stats()
        if not stats:
            return {"status": "warn", "details": "Could not inspect Celery worker stats."}

        return {"status": "ok", "details": f"Found {len(workers)} active worker(s)."}
    except Exception as e:
        return {"status": "error", "details": f"Celery connection error: {e}"}

def check_embedding_provider() -> HealthStatus:
    """Checks the status of the currently active embedding provider."""
    from vectorsearch.models import EmbeddingVersion
    from vectorsearch.providers.utils import get_provider_instance

    active_version = EmbeddingVersion.objects.filter(is_active=True).first()
    if not active_version:
        return {"status": "warn", "details": "No active embedding provider is configured."}

    try:
        provider = get_provider_instance(active_version)
        # In a real scenario, this might be a `provider.health_check()` call.
        # For now, we just check if we can instantiate it.
        return {"status": "ok", "details": f"Provider '{active_version.provider}/{active_version.model_name}' is active."}
    except Exception as e:
        return {"status": "error", "details": f"Failed to initialize embedding provider: {e}"}

def get_system_health() -> dict[str, HealthStatus]:
    """Aggregates the health status of all critical services."""
    return {
        "database": check_postgres(),
        "redis": check_redis(),
        "celery_workers": check_celery_workers(),
        "embedding_provider": check_embedding_provider(),
    }

def get_connectors_health() -> list[dict]:
    """Retrieves the health status of all defined connectors."""
    connectors = Connector.objects.all()
    return [
        {
            "type": conn.get_type_display(),
            "status": conn.status,
            "last_sync_at": conn.last_sync_at,
            "last_error": conn.last_error_message,
        }
        for conn in connectors
    ]
