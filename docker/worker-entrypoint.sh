#!/bin/bash
set -e
echo "🔄 Starting Pharmaviyum Worker..."
# Wait for Redis

echo "⏳ Waiting for Redis..."
while ! redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
   echo "  Redis is unavailable - sleeping"
   sleep 1
done
echo "✅ Redis is ready!"
# Execute the worker

echo "✨ Starting worker process..."
exec python -m src.pharmaviyum.workers.worker "$@"
