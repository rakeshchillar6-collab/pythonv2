# SEO Studio Runbook

This document provides guidance for developers and operators on common tasks, workflows, and troubleshooting for the production-ready SEO Studio application.

## Core Architecture

-   **Services:** The system is composed of several key services orchestrated by Docker Compose: `db` (Postgres), `redis`, `web` (Gunicorn/Django), multiple `worker` services for different Celery queues, and a `beat` scheduler.
-   **Multi-tenancy:** Data is strictly isolated at the application level. A `SiteMiddleware` attaches a `request.site` object to every request, and custom `SiteManager`s on core models ensure all database queries are automatically filtered by `site_id`.
-   **Asynchronous Tasks:** Celery is used extensively. There are multiple queues to ensure high-priority tasks (e.g., publishing) are not blocked by long-running, low-priority tasks (e.g., SERP collection, embeddings).
    -   `default`: General, low-volume tasks.
    -   `embeddings`: For CPU-intensive vector embedding calculations.
    -   `serp`: For I/O-bound SERP scraping.
    -   `publishing`: For time-sensitive content publishing jobs.
    -   `reports`: For potentially long-running analytical queries.

## Common Operations

### Scaling Services

-   **Web Workers:** To handle more HTTP traffic, scale the `web` service:
    `docker compose up -d --scale web=3`
-   **Celery Workers:** To increase throughput for a specific task type, scale the corresponding worker. For example, to add more publishing workers:
    `docker compose up -d --scale worker_publishing=4`

### Secret Rotation

1.  **Update the Secret:** Change the secret value in your secrets management system (e.g., HashiCorp Vault, AWS Secrets Manager).
2.  **Update Environment:** Update the `.env` file or the environment variables in your container orchestration platform.
3.  **Restart Services:** Perform a rolling restart of the `web` and `worker` services.
    `docker compose restart web worker_default worker_embeddings worker_publishing`

### Database Backup and Restore

-   **RPO:** 15 minutes. **RTO:** 30 minutes.
-   **Create a Backup:**
    `docker compose exec db pg_dump -U <user> -d <dbname> | gzip > backup.sql.gz`
-   **Restore from Backup:**
    1.  Stop the web/worker services: `docker compose stop web worker_*`
    2.  Restore the data: `gunzip < backup.sql.gz | docker compose exec -T db psql -U <user> -d <dbname>`
    3.  Restart services: `docker compose start web worker_*`

### Managing Celery Queues

-   **Purge a Queue:** To clear all tasks from a specific queue (e.g., `serp`):
    `docker compose exec worker_default celery -A seo_studio purge -Q serp`
-   **Replay Failed Jobs:** (Requires Dead-Letter Queue setup)
    1.  Inspect jobs in the DLQ.
    2.  Use a custom management command (`python manage.py replay_failed_jobs --queue=...`) to re-queue them.

### Rebuilding Indexes

-   **Vector Indexes:** If embedding models change, you may need to re-index.
    1.  Open a shell: `make shell`
    2.  Run the re-embedding task via Django shell or a custom management command.

## Troubleshooting Playbook

### High API Latency

1.  **Check Metrics:** Look at the "System Health" dashboard. Is `api_p95_latency` high?
2.  **Check Logs:** Look for slow queries in the structured logs. Use the `request_id` to trace a slow request.
3.  **Check DB:** Use `EXPLAIN ANALYZE` on the slow query to identify missing indexes or inefficient joins.
4.  **Check Redis:** Is Redis memory pressure high? Is it slow to respond?

### Celery Queues are Growing

1.  **Check Health Dashboard:** Identify which queue is growing.
2.  **Check Worker Logs:** Are the workers for that queue healthy? Are they reporting errors?
3.  **Scale Up:** If workers are healthy but overwhelmed, scale them up (see "Scaling Services").
4.  **Check Dependencies:** Is the queue blocked by an external service (e.g., SERP API, OpenAI)? Check the Circuit Breaker status if implemented.

### Integration Failures (e.g., GSC, SERP API)

1.  **Check Health Monitor:** The "Integrations Health" panel should show the status of external providers.
2.  **Check Logs:** Look for logs from the relevant integration (e.g., `integrations.services.gsc`, `metaphorge.tasks.serp`).
3.  **Check Credentials:** Have API keys or tokens expired?
4.  **Engage Circuit Breaker:** If a provider is down, the Circuit Breaker should trip automatically. You can manually trip it via an ops endpoint if needed.
