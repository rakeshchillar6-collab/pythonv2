# SEO Studio

SEO Studio is a comprehensive, data-driven Content Management System (CMS) designed for SEO professionals and content teams. It integrates advanced analytics, semantic search, and strategic planning tools directly into the content workflow.

This project is a monorepo containing the full stack for the SEO Studio application, built with a Django/DRF backend and a Next.js frontend.

## Key Features

-   **Modular Django Backend:** A scalable backend powered by Django and Django Rest Framework.
-   **Vector Search:** Built-in semantic search capabilities using PostgreSQL and the `pgvector` extension.
-   **Intelligence Layer:** Automated alerts for performance drops, topical authority modeling, and internal link equity calculation (PageRank).
-   **Dynamic Admin Panel:** A fast, responsive admin interface built with Django templates and **HTMX**.
-   **Asynchronous Task Processing:** Uses Celery and Redis for handling long-running background jobs like data integration syncs and report generation.
-   **Decoupled Frontend:** A modern, performant public-facing website built with Next.js.
-   **Containerized Environment:** The entire stack is managed with Docker and Docker Compose for easy setup and consistent development environments.

## Getting Started

This project is designed to be run using Docker. For a complete guide on how to set up your local development environment, please see the installation instructions.

➡️ **[Full Installation Guide](./docs/INSTALL.md)**

### Quick Start

1.  **Clone the repo:** `git clone <repository_url>`
2.  **Set up environment:** `cp infra/env/.env.example infra/env/.env`
3.  **Start services:** `make up`
4.  **Run migrations:** `make migrate`
5.  **Create a superuser:** `make shell` then `python manage.py createsuperuser`
6.  **Access the admin:** [http://localhost:8000/adminui/](http://localhost:8000/adminui/)

## Documentation

-   **[Installation Guide](./docs/INSTALL.md):** Step-by-step instructions for setting up the development environment.
-   **[Runbook](./docs/RUNBOOK.md):** A guide for developers on common operational tasks, project architecture, and troubleshooting.
-   **[ADRs](./docs/ADRs/):** (Architectural Decision Records) A place to document key architectural choices.

## Project Structure

-   `seo-studio/`: Project root.
    -   `apps/`: Contains the main applications.
        -   `web/`: The Django backend project.
        -   `next/`: The Next.js frontend project.
    -   `infra/`: Infrastructure configuration.
        -   `docker/`: Dockerfiles for each service.
        -   `docker-compose.yml`: Main Docker Compose file.
        -   `env/`: Environment variable files.
    -   `docs/`: Project documentation.
    -   `packages/`: Shared libraries or components (e.g., a Python SDK, UI components).
    -   `Makefile`: Convenience scripts for development.
