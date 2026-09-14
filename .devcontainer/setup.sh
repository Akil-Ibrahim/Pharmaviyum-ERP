#!/bin/bash
# ============================================================================
# Codespaces Setup Script
# ============================================================================

echo "🚀 Setting up Pharmaviyum AI in Codespaces..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements-ai.txt

# Start PostgreSQL and Redis (not Ollama - no GPU in Codespaces)
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose -f docker-compose.codespaces.yml up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Services:"
docker-compose -f docker-compose.codespaces.yml ps

echo ""
echo "🌐 URLs:"
echo "  - API: https://<codespace-name>-8000.app.github.dev"
echo "  - Docs: https://<codespace-name>-8000.app.github.dev/docs"
echo ""
echo "️  IMPORTANT: Set your LLM API keys in .env:"
echo "  - GROQ_API_KEY (recommended for Codespaces)"
echo "  - or OPENAI_API_KEY"
echo "  - or ANTHROPIC_API_KEY"
echo ""
echo "📝 Edit .env and run: docker-compose -f docker-compose.codespaces.yml restart api"
