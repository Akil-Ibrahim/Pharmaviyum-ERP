#!/bin/bash
# Codespaces setup for Pharmaviyum ERP/CRM.
set -euo pipefail

echo "🚀 Setting up Pharmaviyum in Codespaces..."

if ! command -v uv >/dev/null 2>&1; then
  python -m pip install --user uv
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "📦 Installing project and development dependencies..."
uv sync --frozen

echo "🐳 Starting PostgreSQL and Redis..."
docker compose -f docker-compose.codespaces.yml up -d postgres redis

echo "⏳ Waiting for services..."
sleep 10

echo "🗄️ Running database migrations..."
uv run alembic upgrade head

echo
echo "✅ Setup complete!"
docker compose -f docker-compose.codespaces.yml ps
echo
echo "API: https://<codespace-name>-8000.app.github.dev"
echo "Docs: https://<codespace-name>-8000.app.github.dev/docs"
echo
echo "Configure the required LLM API keys in your environment."
