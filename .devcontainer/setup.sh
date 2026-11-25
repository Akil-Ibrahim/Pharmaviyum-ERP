#!/usr/bin/env bash
# Install the locked Python dependencies in the Compose-backed Dev Container.
set -euo pipefail

cd /workspaces/Pharmaviyum-ERP

echo "Checking the development toolchain..."
command -v uv >/dev/null 2>&1 || {
  echo "uv is missing from the Dev Container image. Rebuild the Dev Container." >&2
  exit 1
}

python --version
uv --version

echo "Installing locked project and development dependencies..."
uv sync --frozen

echo
echo "Dev Container setup complete."
echo "PostgreSQL: postgres:5432"
echo "Redis: redis:6379"
echo "Start the API when needed with:"
echo "  uv run uvicorn src.pharmaviyum.main:app --reload --host 0.0.0.0 --port 8000"
