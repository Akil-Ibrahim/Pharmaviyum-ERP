#!/bin/bash
# Docker start script for Pharmaviyum-CRM

set -e

echo "🐳 Starting Pharmaviyum-CRM with Docker..."
echo ""
echo "Services exposed by docker-compose.yml:"
echo "  - Web UI / API: http://localhost:8000"
echo "  - API docs:     http://localhost:8000/docs"
echo "  - PostgreSQL:   localhost:5432"
echo "  - Redis:        localhost:6379"
echo "  - Ollama:       http://localhost:11434"
echo "  - Jaeger UI:    http://localhost:16686"
echo "  - OTLP gRPC:    localhost:4317"
echo "  - OTLP HTTP:    localhost:4318"
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

# Ensure the script runs from the repository root so docker compose can find docker-compose.yml
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Build and start services
docker compose up --build

echo ""
echo "✅ Services stopped"
