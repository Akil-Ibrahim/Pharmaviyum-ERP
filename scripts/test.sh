#!/usr/bin/env bash
# Run the repository test suite with the dependency versions pinned in uv.lock.
# Usage: ./scripts/test.sh [unit|integration|all|coverage]

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required. Install it from https://docs.astral.sh/uv/" >&2
    exit 1
fi

COMMAND="${1:-unit}"

echo "Running tests: $COMMAND"

case "$COMMAND" in
    unit)
        uv run --locked pytest tests/ -m unit -v
        ;;
    integration)
        uv run --locked pytest tests/ -m integration -v
        ;;
    all)
        uv run --locked pytest tests/ -v
        ;;
    coverage)
        uv run --locked pytest tests/ --cov=src/pharmaviyum --cov-report=html --cov-report=term-missing -v
        echo "Coverage report: htmlcov/index.html"
        ;;
    *)
        echo "Usage: $0 [unit|integration|all|coverage]" >&2
        exit 2
        ;;
esac
