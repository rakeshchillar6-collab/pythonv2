# SEO Studio Runbook

This document provides guidance for developers and operators on common tasks, workflows, and troubleshooting for the SEO Studio application.

## Development Workflow

A `Makefile` is provided at the root of the repository to simplify common commands.

### Starting and Stopping the Environment

-   **Start all services:** `make up` (runs `docker compose up -d`)
-   **Stop all services:** `make down` (runs `docker compose down`)
-   **View logs:** `make logs` (runs `docker compose logs -f`)
-   **Rebuild containers:** `make build` (runs `docker compose build`)

### Working with the Database

-   **Apply migrations:** `make migrate`
-   **Create new migrations:** After changing models in a Django app, run `make makemigrations <app_name>`. For example: `make makemigrations content`.
-   **Seed data:** `make seed` (runs the `seed_data` management command). This is safe to run multiple times.

### Running Tests and Linters

-   **Run the full test suite:** `make test`
-   **Get a test coverage report:** `make coverage`
-   **Check code style:** `make lint`

### Accessing the Django Shell

To interact with the Django application directly, you can open a shell inside the `web` container:

```bash
make shell
```

From there, you can run `python manage.py ...` commands or open a Django shell with `python manage.py shell_plus`.

## Architecture Overview

-   **Monorepo Structure:** The project is a monorepo containing the Django backend (`apps/web`), Next.js frontend (`apps/next`), shared packages (`packages/`), and infrastructure configuration (`infra/`).
-   **Services:** The `docker-compose.yml` file orchestrates the following services:
    -   `db`: PostgreSQL database with the `pgvector` extension.
    -   `redis`: Message broker for Celery.
    -   `web`: Gunicorn server for the Django application and Nginx for static files.
    -   `worker`: Celery worker for running background tasks (e.g., GSC sync, report generation).
    -   `beat`: Celery beat for scheduling periodic tasks.
    -   `next`: The Next.js frontend server.

## Key Subsystems

-   **Authentication:** Handled by Django, using `rest_framework_simplejwt` for API authentication with the Next.js frontend.
-   **Admin Panel:** Built with Django templates and **HTMX**. This allows for a dynamic, single-page-application feel without writing extensive JavaScript. Views are in `adminui/views/`, templates in `adminui/templates/`, and URLs in `adminui/urls.py`.
-   **Asynchronous Tasks:** Heavy or long-running operations are offloaded to Celery. This includes:
    -   Syncing data from integrations (GSC, GA).
    -   Running alert detection jobs.
    -   Calculating graph metrics (PageRank).
    -   Generating reports.
-   **Report Builder:** Uses a custom, secure DSL to generate reports from whitelisted models and fields. The core logic resides in `reports/services/`.

## Troubleshooting

### `vector` extension not found

If you see an error related to the `vector` extension not being available, it's likely the initial migration failed or was not run.

1.  Ensure the `db` container is healthy: `docker compose ps`
2.  Run the migration command: `make migrate`

The first migration in the `vectorsearch` app (`0001_initial.py`) contains the `CreateExtension("vector")` operation.

### CORS or CSRF Errors

-   **CORS:** If the Next.js app reports CORS errors, ensure the `CORS_ALLOWED_ORIGINS` setting in `seo_studio/settings/dev.py` includes the correct frontend URL (default is `http://localhost:3000`).
-   **CSRF:** The API uses JWT for authentication, which is stateless and does not require CSRF protection. The admin panel, however, uses Django's session authentication and is protected. Ensure any `POST` requests from HTMX include the `{% csrf_token %}` in the form.

### Celery Tasks Not Running

1.  **Check Worker/Beat Logs:** Use `make logs` and inspect the output from the `worker` and `beat` services.
2.  **Check Redis:** Ensure the `redis` container is running and healthy. You can connect to it via the `web` container if needed for debugging (`redis-cli -h redis`).
3.  **Task Discovery:** Ensure any new tasks have the `@shared_task` decorator and that the module they are in is imported correctly so Celery can discover them.

### Frontend Fails to Connect to API

1.  **Check Network:** Ensure the `web` and `next` containers are on the same Docker network (they are by default).
2.  **Check Environment Variable:** Verify that `NEXT_PUBLIC_API_URL` in `infra/env/.env` is correctly set to the Django container's address from the perspective of the user's browser (e.g., `http://localhost:8000/api/`).
3.  **Check API Health:** Access the API's health check endpoint directly in your browser: `http://localhost:8000/api/health/`. It should return a JSON response with `"status": "ok"`.
