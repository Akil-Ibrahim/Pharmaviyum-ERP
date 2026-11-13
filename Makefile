# =============================================================================
# Pharmaviyum CRM - Makefile
# =============================================================================
# Common commands for local development, testing, and release operations.
# The root docker-compose.yml is the development backend/infrastructure stack.
# The React frontend runs separately from frontend/.
# =============================================================================

.PHONY: help dev dev-detach stop clean clean-volumes test test-cov lint format pre-commit logs logs-api logs-db logs-redis logs-ollama shell-api shell-db shell-redis status rebuild update docs security

.DEFAULT_GOAL := help

# =============================================================================
# Development
# =============================================================================

dev:
	@echo "🚀 Starting development environment..."
	docker compose up --build

dev-detach:
	@echo "🚀 Starting development environment (detached)..."
	docker compose up --build -d

stop:
	@echo "🛑 Stopping development environment..."
	docker compose down

clean:
	@echo "🧹 Stopping the development stack (preserving volumes and backups)..."
	docker compose down --remove-orphans

clean-volumes:
	@if [ "$(CONFIRM_VOLUME_DELETION)" != "1" ]; then \
		echo "Refusing to delete Compose volumes. Re-run with CONFIRM_VOLUME_DELETION=1 only for disposable local data."; \
		exit 2; \
	fi
	@echo "⚠️  Removing local Compose volumes..."
	docker compose down --volumes --remove-orphans

# =============================================================================
# Deployment
# Hosted deployment is managed separately through FastAPI Cloud; local commands stay development-only.

# =============================================================================
# Database
# =============================================================================

migrate:
	@echo "📦 Running database migrations..."
	docker compose exec api alembic upgrade head

migration:
	@echo "📝 Creating new migration..."
	@read -p "Enter migration message: " msg; \
	docker compose exec api alembic revision --autogenerate -m "$$msg"

rollback:
	@echo "⏪ Rolling back last migration..."
	docker compose exec api alembic downgrade -1

# =============================================================================
# Testing & Quality
# =============================================================================

test:
	@echo "🧪 Running tests..."
	uv run --locked pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	uv run --locked pytest --cov=src --cov-report=html

lint:
	@echo "🔍 Running Python quality checks..."
	uv run --locked ruff check .
	uv run --locked black --check .
	uv run --locked isort --check-only .
	uv run --locked mypy --explicit-package-bases src

format:
	@echo "✨ Formatting Python code..."
	uv run --locked black .
	uv run --locked isort .
	uv run --locked ruff check . --fix

pre-commit:
	@echo "🪝 Running pre-commit hooks..."
	pre-commit run --all-files

security:
	@echo "🔒 Running security audit..."
	uv run --locked pip-audit

# =============================================================================
# Logging & Debugging
# =============================================================================

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-db:
	docker compose logs -f postgres

logs-redis:
	docker compose logs -f redis

logs-ollama:
	docker compose logs -f ollama

# =============================================================================
# Shell Access
# =============================================================================

shell-api:
	docker compose exec api /bin/bash

shell-db:
	docker compose exec postgres psql -U postgres -d pharmaviyum

shell-redis:
	docker compose exec redis redis-cli

# =============================================================================
# Utilities
# =============================================================================

status:
	docker compose ps

rebuild:
	@echo "🔨 Rebuilding containers..."
	docker compose build --no-cache

update:
	@echo "📦 Updating Python dependencies..."
	uv sync

# API documentation is served by FastAPI; no generated files are created.
docs:
	@echo "📚 API docs: http://localhost:8000/docs"
	@echo "OpenAPI JSON: http://localhost:8000/openapi.json"

# =============================================================================
# Help
# =============================================================================

help:
	@echo "Pharmaviyum CRM - Available Commands"
	@echo "====================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start development stack"
	@echo "  make dev-detach      - Start development stack in background"
	@echo "  make stop            - Stop development stack"
	@echo "  make clean           - Stop stack; preserve database volumes and backups"
	@echo "  CONFIRM_VOLUME_DELETION=1 make clean-volumes - Delete local Compose volumes (destructive)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          - Apply local migrations"
	@echo "  make migration        - Create a new migration"
	@echo "  make rollback         - Roll back one migration"
	@echo ""
	@echo "Quality:"
	@echo "  make test             - Run backend tests"
	@echo "  make test-cov         - Run tests with coverage"
	@echo "  make lint             - Run CI-aligned Python checks"
	@echo "  make format           - Format Python code"
	@echo "  make pre-commit       - Run pre-commit hooks"
	@echo "  make security         - Run pip-audit"
	@echo ""
	@echo "Debugging:"
	@echo "  make logs             - Follow all Compose logs"
	@echo "  make logs-api         - Follow FastAPI logs"
	@echo "  make logs-db          - Follow PostgreSQL logs"
	@echo "  make logs-redis       - Follow Redis logs"
	@echo "  make logs-ollama      - Follow Ollama logs"
	@echo "  make shell-api        - Open API container shell"
	@echo "  make shell-db         - Open PostgreSQL shell"
	@echo "  make shell-redis      - Open Redis shell"
