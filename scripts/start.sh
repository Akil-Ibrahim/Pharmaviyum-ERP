#!/bin/bash
# ============================================================================
# Start Pharmaviyum AI Stack
# ============================================================================

echo "🚀 Starting Pharmaviyum AI Stack..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
fi

# Start all services
echo "📦 Starting Docker Compose services..."
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo " URLs:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"
echo "  - Metrics: http://localhost:8000/metrics"
echo ""
echo "📋 Logs:"
echo "  docker-compose logs -f api"
echo ""
echo "️  To stop:"
echo "  docker-compose down"
