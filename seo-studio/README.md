# SEO Studio

**SEO Studio** is a modern, modular, and scalable SEO-focused Content Management System (CMS) built with a powerful stack designed for performance and developer experience.

## Core Technologies

-   **Backend**: Django + Django Rest Framework (DRF)
-   **Frontend**: Next.js (App Router)
-   **Database**: PostgreSQL with `pgvector` for semantic search capabilities
-   **Task Queue**: Celery with Redis as the broker
-   **Admin Panel**: Lightweight and interactive admin panel built with HTMX
-   **Containerization**: Fully containerized with Docker and Docker Compose for easy setup and deployment.

## Project Structure

This project is a monorepo containing the following main applications:

-   `apps/web`: The Django backend project, serving the API and the HTMX admin panel.
-   `apps/next`: The Next.js frontend application for the public-facing website.
-   `infra/`: Contains Docker configurations, environment files, and other infrastructure-related code.
-   `docs/`: Project documentation, including installation guides and architectural decisions.

## Features

-   **Modular Architecture**: Django apps are organized by feature (core, content, seo, etc.) for better separation of concerns.
-   **API-First Design**: A robust DRF-based API serves as the backbone for the frontend and any future clients.
-   **Semantic Search**: Leverages `pgvector` to enable powerful semantic search on content embeddings.
-   **Interactive Admin Panel**: A fast, server-rendered admin panel using HTMX, avoiding the complexity of large frontend frameworks for internal tools.
-   **Modern Frontend**: A public site built with Next.js, benefiting from features like Server-Side Rendering (SSR) and Static Site Generation (SSG).
-   **Task Scheduling**: Asynchronous task processing and scheduling with Celery.

## Getting Started

For detailed instructions on how to set up and run the project locally, please refer to the **[Installation Guide](./docs/INSTALL.md)**.

### Quick Start

1.  **Clone the repository.**
2.  **Configure environment variables:** `cp infra/env/.env.example infra/env/.env.dev`
3.  **Run the application:** `docker-compose up --build`
4.  **Apply migrations:** `docker-compose exec web python manage.py migrate`
5.  **Create a superuser:** `docker-compose exec web python manage.py createsuperuser`
6.  **(Optional) Seed the database:** `docker-compose exec web python manage.py seed`

Once set up, the applications will be available at:
-   **Next.js Frontend**: `http://localhost:3000`
-   **Django API / Admin**: `http://localhost:8000`

## Next Steps

This project skeleton is the foundation for a powerful CMS. The next steps for development include:
-   Implementing the `vectorsearch` service to generate and search embeddings.
-   Building out the remaining stubbed-out Django apps (`seo`, `metaphorge`, `integrations`, etc.).
-   Expanding the HTMX admin panel with more features and CRUD interfaces.
-   Enhancing the Next.js frontend with more content types and features.
