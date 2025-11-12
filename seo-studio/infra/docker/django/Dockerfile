# infra/docker/django/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only the files necessary for poetry to install dependencies
COPY ./seo-studio/apps/web/pyproject.toml ./seo-studio/apps/web/poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-dev

# Copy the rest of the application code
COPY ./seo-studio/apps/web /app

# The command to run the application will be passed by docker-compose
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
