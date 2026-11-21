#!/usr/bin/env bash
# Start the repository's Docker Compose development stack in the background.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but not installed." >&2
  exit 1
fi

docker compose up --build -d

cat <<'EOF'
Docker Compose services started.

Endpoints:
  API:      http://localhost:8000
  API docs: http://localhost:8000/docs
  Postgres: localhost:5432
  Redis:    localhost:6379

Logs: docker compose logs -f api
Stop: docker compose down
EOF
