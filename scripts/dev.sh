#!/bin/bash
set -e

echo "🚀 Starting Pharmaviyum CRM in development mode..."

# Build and start services
docker-compose up --build -d

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Endpoints:"
echo "  API:          http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Redis GUI:    http://localhost:8081"
echo "  Database GUI: http://localhost:8082"
echo ""
echo "📊 Logs:"
echo "  docker-compose logs -f api"
echo "  docker-compose logs -f worker"
echo ""
echo "🛑 Stop:"
echo "  docker-compose down"
