# Installation Guide for SEO Studio

This document provides instructions on how to set up and run the SEO Studio project locally using Docker.

## Prerequisites

- Docker
- Docker Compose

## Setup Steps

1.  **Clone the Repository**

    ```bash
    git clone <repository-url>
    cd seo-studio
    ```

2.  **Configure Environment Variables**

    Copy the example environment file to create a local configuration file for development.

    ```bash
    cp infra/env/.env.example infra/env/.env.dev
    ```

    You can modify the values in `infra/env/.env.dev` if needed, but the defaults are suitable for local development.

3.  **Build and Run the Services**

    Use Docker Compose to build the images and start all the services.

    ```bash
    docker-compose -f docker-compose.yml up --build -d
    ```
    This command will start the Django web server, Next.js frontend, PostgreSQL database, Redis, and a Celery worker.

4.  **Apply Database Migrations**

    Once the containers are running, apply the Django database migrations to set up the database schema.

    ```bash
    docker-compose exec web python manage.py migrate
    ```

5.  **Create a Superuser**

    To access the admin panel, you need to create a superuser account.

    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```
    Follow the prompts to set a username, email, and password.

6.  **Seed Initial Data (Optional)**

    To populate the database with some sample data, run the seed script.

    ```bash
    docker-compose exec web python manage.py seed
    ```

## Accessing the Applications

-   **Django API & Admin Panel**: [http://localhost:8000](http://localhost:8000)
-   **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)
-   **API Documentation (Swagger/Redoc)**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

## Stopping the Services

To stop all running containers, use:

```bash
docker-compose down
```
