# Makefile
.PHONY: help up down build logs shell migrate seed test coverage lint

help:
	@echo "Commands:"
	@echo "  up           : Start all services in the background."
	@echo "  down         : Stop and remove all services."
	@echo "  build        : Build or rebuild services."
	@echo "  logs         : Follow logs for all services."
	@echo "  shell        : Open a shell in the Django container."
	@echo "  migrate      : Run Django migrations."
	@echo "  makemigrations: Create new Django migrations."
	@echo "  seed         : Seed the database with initial data."
	@echo "  test         : Run the Django test suite."
	@echo "  coverage     : Run tests and generate a coverage report."
	@echo "  lint         : Run linters (e.g., ruff, black)."

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

shell:
	docker compose exec web bash

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations $(filter-out $@,$(MAKECMDGOALS))

seed:
	docker compose exec web python manage.py seed_data

test:
	docker compose exec web pytest

coverage:
	docker compose exec web pytest --cov=.

lint:
	docker compose exec web ruff check .
	docker compose exec web black . --check

# Allows passing arguments to makemigrations, e.g., `make makemigrations myapp`
%:
	@:
