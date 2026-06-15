#!/bin/bash
# Docker start script for Pharmaviyum-CRM

set -e

echo "🐳 Starting Pharmaviyum-CRM with Docker..."
echo ""
echo "Services will be available at:"
echo "  - Frontend:    http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - AI Service:  http://localhost:8001"
echo "  - Database:    localhost:5432"
echo "  - Redis:       localhost:6379"
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
