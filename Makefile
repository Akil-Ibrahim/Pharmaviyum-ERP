# =============================================================================
# PharmaViyum CRM - Makefile
# =============================================================================
# Common commands for development and deployment
# =============================================================================

.PHONY: help dev prod test lint format clean migrate backup restore logs shell

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# Development Commands
# =============================================================================

## Start development environment
dev:
@echo "🚀 Starting development environment..."
docker compose up --build

## Start development environment in detached mode
dev-detach:
@echo "🚀 Starting development environment (detached)..."
docker compose up --build -d

## Stop development environment
stop:
@echo "🛑 Stopping development environment..."
docker compose down

## Stop and remove volumes
clean:
@echo "🧹 Cleaning up (including volumes)..."
docker compose down -v
rm -rf backups/

# =============================================================================
# Production Commands
# =============================================================================

## Start production environment
prod:
@echo "🚀 Starting production environment..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

## Stop production environment
prod-stop:
@echo "🛑 Stopping production environment..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
## Restart production environment
prod-restart: prod-stop prod

# =============================================================================
# Database Commands
# =============================================================================

## Run database migrations
migrate:
@echo "📦 Running database migrations..."
docker compose exec backend alembic upgrade head

## Create new migration
migration:
@echo "📝 Creating new migration..."
@read -p "Enter migration message: " msg; \
docker compose exec backend alembic revision --autogenerate -m "$$msg"

## Rollback last migration
rollback:
@echo "⏪ Rolling back last migration..."
docker compose exec backend alembic downgrade -1

## Start backup service
backup:
@echo "💾 Starting backup service..."
docker compose -f docker-compose.yml -f docker-compose.backup.yml up -d postgres-backup

## Stop backup service
backup-stop:
@echo "🛑 Stopping backup service..."
docker compose -f docker-compose.yml -f docker-compose.backup.yml down postgres-backup

## Manual backup (immediate)
backup-now:
@echo "💾 Creating manual backup..."
docker compose exec postgres-backup /backup.sh

## Restore database from backup
restore:
@echo "⚠️  This will restore the database from backup!"
@read -p "Are you sure? [y/N] " confirm; \
if [ "$$confirm" = "y" ]; then \
echo "🔄 Restoring database..."; \
docker compose exec postgres-backup /restore.sh; \
else \
echo "❌ Cancelled"; \
fi
# =============================================================================
# Testing & Quality
# =============================================================================

## Run tests
test:
@echo "🧪 Running tests..."
docker compose exec backend pytest tests/ -v

## Run tests with coverage
test-cov:
@echo "🧪 Running tests with coverage..."
docker compose exec backend pytest tests/ --cov=src --cov-report=html

## Run linter
lint:
@echo "🔍 Running linter..."
docker compose exec backend ruff check src/
docker compose exec backend mypy src/

## Format code
format:
@echo "✨ Formatting code..."
docker compose exec backend ruff format src/
docker compose exec backend ruff check --fix src/

## Run pre-commit hooks
pre-commit:
@echo "🪝 Running pre-commit hooks..."
pre-commit run --all-files

# =============================================================================
# Logging & Debugging
# =============================================================================

## View logs (all services)
logs:
docker compose logs -f

## View backend logs
logs-backend:
docker compose logs -f backend

## View frontend logs
logs-frontend:
docker compose logs -f frontend

## View AI service logs
logs-ai:
docker compose logs -f mortarium-ai
## View database logs
logs-db:
docker compose logs -f postgres

# =============================================================================
# Shell Access
# =============================================================================

## Open backend shell
shell-backend:
docker compose exec backend /bin/bash

## Open frontend shell
shell-frontend:
docker compose exec frontend /bin/sh

## Open database shell (psql)
shell-db:
docker compose exec postgres psql -U postgres -d pharmaviyum

## Open Redis shell
shell-redis:
docker compose exec redis redis-cli

# =============================================================================
# Utility Commands
# =============================================================================

## Show container status
status:
docker compose ps

## Rebuild containers
rebuild:
@echo "🔨 Rebuilding containers..."
docker compose build --no-cache

## Update dependencies
update:
@echo "📦 Updating dependencies..."
docker compose exec backend pip install --upgrade -r requirements.txt
docker compose exec frontend pnpm update

## Generate API documentation
docs:
@echo "📚 Generating API documentation..."
@echo "API docs available at: http://localhost:8000/docs"
@echo "OpenAPI JSON: http://localhost:8000/openapi.json"
## Security audit
security:
@echo "🔒 Running security audit..."
docker compose exec backend pip-audit
docker compose exec frontend pnpm audit

# =============================================================================
# Help
# =============================================================================

## Show this help message
help:
@echo "PharmaViyum CRM - Available Commands"
@echo "====================================="
@echo ""
@echo "Development:"
@echo "  make dev              - Start development environment"
@echo "  make dev-detach       - Start dev environment (detached)"
@echo "  make stop             - Stop development environment"
@echo "  make clean            - Stop and remove volumes"
@echo ""
@echo "Production:"
@echo "  make prod             - Start production environment"
@echo "  make prod-stop        - Stop production environment"
@echo "  make prod-restart     - Restart production environment"
@echo ""
@echo "Database:"
@echo "  make migrate          - Run database migrations"
@echo "  make migration        - Create new migration"
@echo "  make rollback         - Rollback last migration"
@echo "  make backup           - Start backup service"
@echo "  make backup-now       - Create manual backup"
@echo "  make restore          - Restore from backup"
@echo ""
@echo "Testing & Quality:"
@echo "  make test             - Run tests"
@echo "  make test-cov         - Run tests with coverage"
@echo "  make lint             - Run linter"
@echo "  make format           - Format code"
@echo ""
@echo "Logging:"
@echo "  make logs             - View all logs"
@echo "  make logs-backend     - View backend logs"
@echo "  make logs-frontend    - View frontend logs"
@echo ""
@echo "Shell Access:"
@echo "  make shell-backend    - Open backend shell"
@echo "  make shell-frontend   - Open frontend shell"
@echo "  make shell-db         - Open database shell"
@echo \"\"@echo "Utility:"
@echo "  make status           - Show container status"
@echo "  make rebuild          - Rebuild containers"
@echo "  make security         - Run security audit"
@echo ""
