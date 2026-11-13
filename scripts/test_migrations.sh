#!/usr/bin/env bash
# Exercise the complete Alembic migration lifecycle on a disposable database only.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "${ALLOW_DESTRUCTIVE_MIGRATION_TESTS:-}" != "1" ]]; then
  echo "Refusing to run: set ALLOW_DESTRUCTIVE_MIGRATION_TESTS=1 to confirm this destructive test." >&2
  exit 2
fi

if [[ -z "${MIGRATION_TEST_DATABASE_URL:-}" ]]; then
  echo "MIGRATION_TEST_DATABASE_URL is required; DATABASE_URL is never used as a fallback." >&2
  exit 2
fi

if [[ -n "${DATABASE_URL:-}" && "${MIGRATION_TEST_DATABASE_URL}" == "${DATABASE_URL}" ]]; then
  echo "Refusing to run: migration test URL must not equal DATABASE_URL." >&2
  exit 2
fi

case "$MIGRATION_TEST_DATABASE_URL" in
  postgres://*|postgresql://*|postgresql+asyncpg://*) ;;
  *)
    echo "MIGRATION_TEST_DATABASE_URL must be a PostgreSQL URL." >&2
    exit 2
    ;;
esac

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

echo "Testing migrations against the explicitly configured disposable database..."
echo "Current revision:"
uv run --locked alembic current

echo "Upgrade to head..."
uv run --locked alembic upgrade head

echo "Downgrade to base (drops all migrated tables)..."
uv run --locked alembic downgrade base

echo "Upgrade to head again..."
uv run --locked alembic upgrade head

echo "Final revision:"
uv run --locked alembic current
echo "Migration lifecycle test completed."
