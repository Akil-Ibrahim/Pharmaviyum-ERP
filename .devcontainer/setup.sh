#!/bin/bash
# Codespaces setup for Pharmaviyum ERP/CRM.
set -euo pipefail

echo "🚀 Setting up Pharmaviyum in Codespaces..."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI is unavailable. Rebuild this Codespace with the configured Docker-in-Docker feature." >&2
  exit 1
fi

echo "⏳ Waiting for the Docker daemon..."
for attempt in {1..60}; do
  if docker info >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" -eq 60 ]]; then
    echo "Docker daemon did not become ready. Rebuild this Codespace and inspect the devcontainer logs." >&2
    exit 1
  fi
  sleep 2
done

if ! command -v uv >/dev/null 2>&1; then
  python -m pip install --user uv
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "📦 Installing project and development dependencies..."
uv sync --frozen

COMPOSE_FILE="docker-compose.codespaces.yml"

echo "🐳 Building and starting the Pharmaviyum stack..."
docker compose -f "$COMPOSE_FILE" up -d --build --wait --wait-timeout 300 \
  postgres redis api celery-worker

echo "🔎 Checking API health..."
for attempt in {1..60}; do
  if curl --fail --silent http://localhost:8000/health >/dev/null; then
    break
  fi
  if [[ "$attempt" -eq 60 ]]; then
    echo "API health check failed. Recent API logs:" >&2
    docker compose -f "$COMPOSE_FILE" logs --tail 100 api >&2
    exit 1
  fi
  sleep 2
done

echo
echo "✅ Setup complete!"
docker compose -f "$COMPOSE_FILE" ps
echo
echo "API: https://<codespace-name>-8000.app.github.dev"
echo "Docs: https://<codespace-name>-8000.app.github.dev/docs"
echo
echo "Configure an LLM provider key to enable AI/RAG features."
