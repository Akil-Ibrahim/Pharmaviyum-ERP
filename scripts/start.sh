#!/bin/sh
set -e

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Starting Pharmaviyum API..."
exec uvicorn src.pharmaviyum.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
