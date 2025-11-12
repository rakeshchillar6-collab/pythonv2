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

def get_system_health() -> dict[str, HealthStatus]:
    """Aggregates the health status of all critical services."""
    return {
        "database": check_postgres(),
        "redis": check_redis(),
        "celery_workers": check_celery_workers(),
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
