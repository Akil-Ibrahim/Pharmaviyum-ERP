#!/bin/bash
# Run the main Pharmaviyum-CRM Docker containers.
# This script starts the core services needed for local development.

set -euo pipefail

echo "🚀 Starting Pharmaviyum-CRM main Docker services..."

echo "Checking Docker availability..."
if ! command -v docker > /dev/null 2>&1; then
  echo "❌ Docker CLI is not installed or not available in PATH."
  exit 1
fi

echo "Building and starting services: db, redis, backend, frontend, mortarium-ai, nginx"
docker compose up -d --build db redis backend frontend mortarium-ai nginx

echo ""
echo "✅ Main services started. Status:"
docker compose ps

echo ""
echo "To follow logs, run: docker compose logs -f backend frontend mortarium-ai nginx"
