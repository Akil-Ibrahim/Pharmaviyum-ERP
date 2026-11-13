#!/bin/bash
set -e
echo "🚀 Starting Pharmaviyum CRM API..."
# Wait for database to be ready

echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -q; do
   echo "  PostgreSQL is unavailable - sleeping"
   sleep 1
done
echo "✅ PostgreSQL is ready!"
# Wait for Redis

echo "⏳ Waiting for Redis..."
while ! redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
   echo "  Redis is unavailable - sleeping"
   sleep 1
done
echo "✅ Redis is ready!"
# Run database migrations

echo "🔄 Running database migrations..."
alembic upgrade head || echo "⚠️  Migration failed or already up to date"
# Execute the main command

echo "✨ Starting application..."
exec "$@"
