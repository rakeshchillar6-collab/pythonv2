# Makefile for seo-studio project

.PHONY: help up down logs migrate superuser seed test worker beat

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  up           Build and start all services in detached mode."
	@echo "  down         Stop and remove all services."
	@echo "  logs         Follow logs for all services."
	@echo "  logs-web     Follow logs for the web (Django) service."
	@echo "  migrate      Apply database migrations."
	@echo "  superuser    Create a new superuser."
	@echo "  seed         Seed the database with initial demo data."
	@echo "  test         Run pytest tests for the Django application."
	@echo "  worker       Start the Celery worker."
	@echo "  beat         Start the Celery beat scheduler."
	@echo "  shell        Open a shell in the web container."

up:
	@echo "Starting up services..."
	docker compose up --build -d

down:
	@echo "Stopping services..."
	docker compose down

logs:
	@echo "Following logs..."
	docker compose logs -f

logs-web:
	@echo "Following web logs..."
	docker compose logs -f web

migrate:
	@echo "Applying database migrations..."
	docker compose exec web python manage.py migrate

superuser:
	@echo "Creating a superuser..."
	docker compose exec web python manage.py createsuperuser

seed:
	@echo "Seeding the database with demo data..."
	docker compose exec web python manage.py seed

test:
	@echo "Running tests..."
	docker compose exec web pytest

worker:
	@echo "Starting Celery worker..."
	docker compose exec web celery -A seo_studio worker --loglevel=info

beat:
	@echo "Starting Celery beat..."
	docker compose exec web celery -A seo_studio beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

shell:
	@echo "Opening shell in web container..."
	docker compose exec web /bin/bash
