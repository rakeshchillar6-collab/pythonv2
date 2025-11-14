# SEO Studio Installation Guide

This guide provides instructions for setting up the SEO Studio monorepo for local development.

## Prerequisites

- **Docker & Docker Compose:** Ensure you have Docker Engine and Docker Compose installed on your system. This is the primary requirement for running the application stack.
- **Git:** For cloning the repository.
- **Make (Optional):** A `Makefile` is provided for convenience. If you don't have `make`, you can run the `docker compose` commands directly.

## 1. Clone the Repository

First, clone the project repository from GitHub to your local machine:

```bash
git clone <repository_url>
cd seo-studio
```

## 2. Set Up Environment Variables

The project uses environment variables for configuration. An example file is provided in the `infra/env/` directory.

1.  **Copy the example file:**

    ```bash
    cp infra/env/.env.example infra/env/.env
    ```

2.  **Review and customize `.env`:**

    Open `infra/env/.env` in your editor. The default values are suitable for local development. Key variables you might want to review are:

    -   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Credentials for the PostgreSQL database.
    -   `DJANGO_SECRET_KEY`: A secret key for Django. A default is provided, but you can generate a new one.
    -   `NEXT_PUBLIC_API_URL`: The URL for the Next.js frontend to communicate with the Django API. The default `http://localhost:8000/api/` should work with the default Docker Compose setup.

## 3. Build and Start the Services

With Docker running, you can build the container images and start all the services (Django, Next.js, Postgres, Redis, Celery) using the `Makefile` or `docker compose`.

**Using Make (Recommended):**

```bash
make build
make up
```

**Using Docker Compose:**

```bash
docker compose build
docker compose up -d
```

The services will now be running in the background. You can check their status with `docker compose ps`.

## 4. Initialize the Database

Once the containers are running, you need to apply the database migrations to set up the schema.

**Using Make:**

```bash
make migrate
```

**Using Docker Compose:**

```bash
docker compose exec web python manage.py migrate
```

This command will also create the `vector` extension in PostgreSQL, as defined in the initial migration.

## 5. Create a Superuser

To access the admin panel, you need to create a superuser account.

**Using Make:**

```bash
make shell
```

Then, inside the container's shell:

```bash
python manage.py createsuperuser
```

Follow the prompts to set up your email, password, and other details.

**Using Docker Compose directly:**

```bash
docker compose exec web python manage.py createsuperuser
```

## 6. Seed the Database (Optional but Recommended)

To populate the application with initial sample data (a test site, users, posts, categories), you can run the seed command.

**Using Make:**

```bash
make seed
```

**Using Docker Compose:**

```bash
docker compose exec web python manage.py seed_data
```

## 7. Accessing the Applications

You're all set up! You can now access the different parts of the application:

-   **Django API:** [http://localhost:8000/api/](http://localhost:8000/api/)
-   **Django Admin UI (HTMX):** [http://localhost:8000/adminui/](http://localhost:8000/adminui/)
-   **Next.js Frontend:** [http://localhost:3000/](http://localhost:3000/)

You can log into the Admin UI with the superuser credentials you created in step 5.
