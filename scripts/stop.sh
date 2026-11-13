#!/usr/bin/env bash
# Stop the local Pharmaviyum Docker Compose stack without deleting data.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI is not installed or not available in PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 (docker compose) is required." >&2
  exit 1
fi

echo "Stopping the development stack; named volumes and backups will be preserved."
docker compose down --remove-orphans

echo
echo "Services stopped. Database volumes and backup files were preserved."
echo "To intentionally delete disposable local volumes, run:"
echo "  CONFIRM_VOLUME_DELETION=1 make clean-volumes"
