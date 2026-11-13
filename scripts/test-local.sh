#!/usr/bin/env bash
# Run the full Python test suite with coverage using the repository's locked dev dependencies.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

echo "Running Python tests with coverage from uv.lock..."
uv run --locked pytest tests/ \
  --cov=src/pharmaviyum \
  --cov-report=html \
  --cov-report=term-missing \
  -v

echo "Coverage report: htmlcov/index.html"
