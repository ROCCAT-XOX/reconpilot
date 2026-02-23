.PHONY: help dev up down build migrate seed test lint format

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start development environment
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

up: ## Start production environment
	docker compose up -d --build

down: ## Stop all containers
	docker compose down

build: ## Build all containers
	docker compose build

migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed database with initial data
	docker compose exec backend python scripts/seed_db.py

test: ## Run backend tests (local)
	cd backend && .venv/bin/python -m pytest tests/ -v

test-docker: ## Run backend tests (via Docker)
	docker compose exec backend pytest -v

test-cov: ## Run backend tests with coverage
	cd backend && .venv/bin/python -m pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Run linters
	cd backend && ruff check .
	cd frontend && npm run lint

format: ## Format code
	cd backend && ruff format .
	cd frontend && npm run format

logs: ## Show logs
	docker compose logs -f

backend-shell: ## Open backend shell
	docker compose exec backend bash

db-shell: ## Open database shell
	docker compose exec postgres psql -U reconforge -d reconforge

redis-cli: ## Open Redis CLI
	docker compose exec redis redis-cli
