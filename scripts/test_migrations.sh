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

# Require a clearly test-named database and a loopback host by default.
# Remote test hosts must be explicitly allowlisted by exact hostname.
URL_INFO="$(python3 -c '
import os
import sys
from urllib.parse import unquote, urlsplit

url = urlsplit(sys.argv[1])
if url.scheme not in {"postgres", "postgresql", "postgresql+asyncpg"}:
    raise SystemExit("MIGRATION_TEST_DATABASE_URL must use PostgreSQL.")
name = unquote(url.path.lstrip("/").split("/", 1)[0])
host = (url.hostname or "").lower()
if not name:
    raise SystemExit("MIGRATION_TEST_DATABASE_URL must include a database name.")
if not host:
    raise SystemExit("MIGRATION_TEST_DATABASE_URL must include an explicit hostname.")

if host not in {"localhost", "127.0.0.1", "::1"}:
    allowed = {
        item.strip().lower()
        for item in os.environ.get("MIGRATION_TEST_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    }
    if host not in allowed:
        raise SystemExit(
            f"database host {host!r} is not loopback; add this exact disposable-test "
            "hostname to MIGRATION_TEST_ALLOWED_HOSTS only after verifying the target."
        )

if "test" not in name.lower() and "testing" not in name.lower():
    raise SystemExit("database name must contain 'test' or 'testing'.")
print(name)
print(host)
' "$MIGRATION_TEST_DATABASE_URL")" || fail "invalid or unsafe PostgreSQL URL."

mapfile -t URL_PARTS <<< "$URL_INFO"
DATABASE_NAME="${URL_PARTS[0]:-}"
DATABASE_HOST="${URL_PARTS[1]:-}"

[[ -n "$DATABASE_NAME" && -n "$DATABASE_HOST" ]] ||
  fail "could not extract the test database name and host."

if ! command -v uv >/dev/null 2>&1; then
  fail "uv is required. Install it from https://docs.astral.sh/uv/"
fi

echo "Testing migrations against test database '$DATABASE_NAME' on '$DATABASE_HOST'..."
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
