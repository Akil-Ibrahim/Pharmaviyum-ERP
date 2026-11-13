#!/usr/bin/env bash
# Exercise the complete Alembic migration lifecycle on a disposable database only.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "Refusing to run migration lifecycle test: $*" >&2
  exit 2
}

[[ "${ALLOW_DESTRUCTIVE_MIGRATION_TESTS:-}" == "1" ]] ||
  fail "set ALLOW_DESTRUCTIVE_MIGRATION_TESTS=1 to explicitly confirm the destructive test."

[[ -n "${MIGRATION_TEST_DATABASE_URL:-}" ]] ||
  fail "MIGRATION_TEST_DATABASE_URL is required; DATABASE_URL is never used as a fallback."

[[ "${MIGRATION_TEST_DATABASE_URL}" != "${DATABASE_URL:-}" ]] ||
  fail "migration test URL must not equal DATABASE_URL."

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 is required to validate the database URL."
fi

# A separate URL and explicit opt-in are not sufficient by themselves:
# require a clearly test-named database so a production database name is rejected.
DATABASE_NAME="$(python3 -c '
import sys
from urllib.parse import unquote, urlsplit

url = urlsplit(sys.argv[1])
if url.scheme not in {"postgres", "postgresql", "postgresql+asyncpg"}:
    raise SystemExit("MIGRATION_TEST_DATABASE_URL must use PostgreSQL.")
name = unquote(url.path.lstrip("/").split("/", 1)[0])
if not name:
    raise SystemExit("MIGRATION_TEST_DATABASE_URL must include a database name.")
print(name)
' "$MIGRATION_TEST_DATABASE_URL")" || fail "invalid PostgreSQL URL."

if [[ ! "$DATABASE_NAME" =~ (^|[-_])(test|testing)([-_]|$) && ! "$DATABASE_NAME" =~ (test|testing)$ ]]; then
  fail "database name '$DATABASE_NAME' is not clearly test-scoped; use a dedicated name such as pharmaviyum_test."
fi

if ! command -v uv >/dev/null 2>&1; then
  fail "uv is required. Install it from https://docs.astral.sh/uv/"
fi

echo "Testing migrations against explicitly configured test database '$DATABASE_NAME'..."
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
