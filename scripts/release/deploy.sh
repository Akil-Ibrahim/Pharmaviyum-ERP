#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy one immutable application image to a Docker Compose host.
# Migrations run before switching the API. A failed migration never replaces the
# running application. After a successful migration, application rollback is
# only attempted when the new container fails its health gate; schema rollback
# is deliberately not automatic.

: "${APP_IMAGE:?APP_IMAGE must be set to an immutable GHCR image reference}"
: "${DATABASE_URL:?DATABASE_URL must be set}"
: "${PGVECTOR_DATABASE_URL:?PGVECTOR_DATABASE_URL must be set}"
: "${REDIS_URL:?REDIS_URL must be set}"
: "${OLLAMA_BASE_URL:?OLLAMA_BASE_URL must be set}"

COMPOSE_FILE="${COMPOSE_FILE:-deploy/docker-compose.release.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-pharmaviyum}"
RELEASE_HEALTH_URL="${RELEASE_HEALTH_URL:-http://127.0.0.1:8000/health}"

export APP_IMAGE DATABASE_URL PGVECTOR_DATABASE_URL REDIS_URL OLLAMA_BASE_URL
export ENVIRONMENT="${ENVIRONMENT:-staging}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-}"
export OLLAMA_FAST_MODEL="${OLLAMA_FAST_MODEL:-qwen2.5:1.5b}"
export OLLAMA_MAIN_MODEL="${OLLAMA_MAIN_MODEL:-qwen2.5:7b}"
export OLLAMA_COMPLEX_MODEL="${OLLAMA_COMPLEX_MODEL:-qwen2.5:72b}"
export OLLAMA_EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL:-mxbai-embed-large}"
export LANGSMITH_ENABLED="${LANGSMITH_ENABLED:-false}"
export LANGSMITH_API_KEY="${LANGSMITH_API_KEY:-}"
export LANGSMITH_PROJECT="${LANGSMITH_PROJECT:-pharmaviyum-staging}"
export OTEL_ENABLED="${OTEL_ENABLED:-false}"
export OTEL_EXPORTER_ENDPOINT="${OTEL_EXPORTER_ENDPOINT:-}"

compose=(docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE")

previous_image=""
if docker inspect pharmaviyum-api >/dev/null 2>&1; then
  previous_image="$(docker inspect --format '{{.Config.Image}}' pharmaviyum-api)"
fi

rollback_app() {
  if [[ -n "$previous_image" && "$previous_image" != "$APP_IMAGE" ]]; then
    echo "Application health gate failed; rolling back application image to $previous_image"
    APP_IMAGE="$previous_image" "${compose[@]}" up -d --no-build api || true
  fi
}

trap 'rollback_app' ERR

echo "Pulling immutable image: $APP_IMAGE"
docker pull "$APP_IMAGE"
echo "Running database migrations before application switch"
"${compose[@]}" --profile migration run --rm migration
echo "Migration completed. Switching API to immutable image"
"${compose[@]}" up -d --no-build api
echo "Waiting for health endpoint: $RELEASE_HEALTH_URL"
for attempt in {1..30}; do
  if curl --fail --silent --show-error "$RELEASE_HEALTH_URL" >/dev/null; then
    trap - ERR
    echo "Release healthy: $APP_IMAGE"
    exit 0
  fi
  sleep 2
done

echo "Release failed health check; application rollback will be attempted"
exit 1
