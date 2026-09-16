#!/bin/bash
# ============================================================================
# Codespaces Setup Script
# ============================================================================

set -euo pipefail

echo "🚀 Setting up Pharmaviyum AI in Codespaces..."

echo "📦 Installing Python dependencies..."
python -m pip install -r requirements.txt

echo "🐳 Starting PostgreSQL and Redis..."
docker compose -f docker-compose.codespaces.yml up -d postgres redis

echo "⏳ Waiting for services..."
sleep 10

echo "🗄️  Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Services:"
docker compose -f docker-compose.codespaces.yml ps

echo ""
echo "🌐 URLs:"
echo "  - API: https://<codespace-name>-8000.app.github.dev"
echo "  - Docs: https://<codespace-name>-8000.app.github.dev/docs"
echo ""
echo "️  IMPORTANT: Configure LLM API keys in your local environment."
echo "  - GROQ_API_KEY (recommended for Codespaces)"
echo "  - or OPENAI_API_KEY"
echo "  - or ANTHROPIC_API_KEY"
echo ""
echo "📝 Restart the API service after changing environment configuration."
