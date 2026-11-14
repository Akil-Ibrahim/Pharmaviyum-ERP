#!/usr/bin/env bash
# Start the core services defined by the canonical docker-compose.yml.
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

SERVICES=(postgres redis api)

echo "Building and starting core services: ${SERVICES[*]}"
docker compose up -d --build "${SERVICES[@]}"

echo
echo "Core service status:"
docker compose ps "${SERVICES[@]}"

echo
echo "Follow logs: docker compose logs -f api"
echo "Stop core services: docker compose stop ${SERVICES[*]}"
