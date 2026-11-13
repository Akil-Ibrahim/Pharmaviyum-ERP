#!/bin/bash
# =============================================================================
# PharmaViyum CRM - Backend Entrypoint Script
# =============================================================================

set -e

echo "🚀 PharmaViyum CRM Backend Starting..."

# Wait for PostgreSQL with timeout
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" 2>/dev/null; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Run migrations (ignore errors if table doesn't exist)
echo "Running migrations..."
alembic upgrade head || echo "⚠️  Migration skipped or failed"

# Start application
echo "Starting Uvicorn..."
exec uvicorn src.pharmaviyum.main:app \
    --host 0.0.0.0 \
    --port "${UVICORN_PORT:-8000}" \
    --workers "${UVICORN_WORKERS:-2}" \
    --log-level info
