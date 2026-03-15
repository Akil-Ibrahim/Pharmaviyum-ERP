.PHONY: help install dev lint format test migrate run clean

help:
@echo "Available commands:"
@echo "  make install    - Install dependencies"
@echo "  make dev        - Run development server"
@echo "  make lint       - Run linters (ruff, mypy)"
@echo "  make format     - Format code with black/ruff"
@echo "  make test       - Run tests with pytest"
@echo "  make migrate    - Run database migrations"
@echo "  make run        - Run production server"
@echo "  make clean      - Clean cache and temp files"

install:
pip install -e ".[dev,prod]"

dev:
uvicorn src.pharmaviyum.main:app --reload --host 0.0.0.0 --port 8000

lint:
ruff check src/ tests/
mypy src/

format:
ruff format src/ tests/
ruff check --fix src/ tests/

test:
pytest tests/ -v --cov=src --cov-report=html

test-unit:
pytest tests/unit -v -m unit

test-integration:
pytest tests/integration -v -m integration

migrate:
alembic upgrade head

migrate-down:
alembic downgrade -1

migrate-create:
alembic revision --autogenerate -m "auto migration"

run:
gunicorn src.pharmaviyum.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

clean:
find . -type f -name '*.pyc' -delete
find . -type d -name '__pycache__' -delete
find . -type d -name '.pytest_cache' -delete
find . -type d -name '.ruff_cache' -delete
find . -type d -name '.mypy_cache' -delete
rm -rf htmlcov/
rm -rf .coverage
