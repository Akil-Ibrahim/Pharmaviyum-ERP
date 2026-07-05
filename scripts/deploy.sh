#!/bin/bash
set -e

echo "🚀 Deploying Pharmaviyum CRM to production..."

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ Error: .env.prod file not found!"
    echo "Copy .env.prod.example to .env.prod and configure it"
    exit 1
fi

# Load production environment
export $(cat .env.prod | grep -v '^#' | xargs)

# Build production images
echo "📦 Building production images..."
docker-compose -f docker-compose.prod.yml build

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.prod.yml down

# Start production services
echo "🚀 Starting production services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run health check
echo "🏥 Running health check..."
curl -f http://localhost/health || echo "⚠️  Health check failed"

echo ""
echo "✅ Production deployment complete!"
echo ""
echo "📍 Endpoints:"
echo "  API:      https://yourdomain.com"
echo "  Grafana:  http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
