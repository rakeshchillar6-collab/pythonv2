# Installation Guide for SEO Studio

This document provides instructions on how to set up and run the SEO Studio project locally using Docker and a Makefile for convenience.

## Prerequisites

-   Docker
-   Docker Compose
-   `make` (optional, but recommended for easy command execution)

## Setup Steps

### 1. Configure Environment Variables

First, copy the example environment file to create your local development configuration.

```bash
cp infra/env/.env.example infra/env/.env.dev
```

The default values in `.env.dev` are suitable for local development and do not need to be changed.

### 2. Build and Run Services

Use the provided `Makefile` to build and start all services in the background.

```bash
make up
```

This command will:
-   Build the Docker images for the Django and Next.js applications.
-   Start all services (`web`, `next`, `db`, `redis`, `worker`) in detached mode.

*Alternatively, without `make`, you can run:*
`docker compose up --build -d`

### 3. Apply Database Migrations

Once the containers are running, apply the database migrations to set up the schema.

```bash
make migrate
```

*Alternatively, without `make`:*
`docker compose exec web python manage.py migrate`

### 4. Create a Superuser

To access the admin panel, you need a superuser account.

```bash
make superuser
```

Follow the prompts to set an email and password.

*Alternatively, without `make`:*
`docker compose exec web python manage.py createsuperuser`

### 5. Seed Initial Data (Recommended)

To populate the application with sample data (users, roles, posts, categories), run the seed command.

```bash
make seed
```

This will create an `admin` and an `editor` user, along with sample content to explore.

*Alternatively, without `make`:*
`docker compose exec web python manage.py seed`

## Accessing the Applications

-   **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)
-   **HTMX Admin Panel**: [http://localhost:8000/adminui/](http://localhost:8000/adminui/)
-   **API Documentation (Swagger)**: [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)

## Development Workflow

Use the `Makefile` for common development tasks:

-   `make down`: Stop and remove all services.
-   `make logs`: View logs from all services.
-   `make test`: Run the pytest suite for the Django app.
-   `make worker`: Start a Celery worker manually (if not using the service from `docker-compose.yml`).
-   `make shell`: Open a Bash shell inside the Django container for debugging or running commands.
