#!/usr/bin/env bash
# Start the Pharmaviyum backend and frontend for local development.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

if ! command -v bun >/dev/null 2>&1; then
  echo "Bun is required for the frontend. Install it from https://bun.sh/" >&2
  exit 1
fi

echo "📦 Syncing Python dependencies from pyproject.toml and uv.lock..."
uv sync --frozen

if [ ! -d "frontend/shadcn-admin/node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  (cd frontend/shadcn-admin && bun install)
fi

echo "🚀 Starting FastAPI backend on http://localhost:8000..."
uv run uvicorn src.pharmaviyum.main:app --reload --port 8000 &
BACKEND_PID=$!
FRONTEND_PID=""

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 3
echo "🚀 Starting frontend..."
(cd frontend/shadcn-admin && bun run dev) &
FRONTEND_PID=$!

wait
