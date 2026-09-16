#!/usr/bin/env bash
set -euo pipefail

# Guarded runner for the Stage 1 k6 workload.
# Synthetic writes must only target an isolated load-test/staging environment.

BASE_URL="${BASE_URL:-http://localhost:8000}"
OUTPUT_DIR="${LOAD_TEST_OUTPUT_DIR:-artifacts/load-tests}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FILE="${OUTPUT_DIR}/stage1-${TIMESTAMP}.json"

case "${BASE_URL}" in
  *prod*|*production*|*live*)
    echo "Refusing to run load tests against a production-like BASE_URL: ${BASE_URL}" >&2
    exit 2
    ;;
esac

command -v k6 >/dev/null 2>&1 || {
  echo "k6 is required but was not found in PATH." >&2
  exit 127
}

mkdir -p "${OUTPUT_DIR}"

if [[ "${ENABLE_WRITES:-false}" == "true" && -z "${AUTH_TOKEN:-}" ]]; then
  echo "ENABLE_WRITES=true requires AUTH_TOKEN for the synthetic superuser." >&2
  exit 2
fi

if [[ "${ENABLE_WRITES:-false}" == "true" ]]; then
  echo "WARNING: synthetic writes are enabled. Use only a disposable or isolated database."
fi

echo "Running Stage 1 load test against ${BASE_URL}"
echo "JSON output: ${OUTPUT_FILE}"

k6 run --out "json=${OUTPUT_FILE}" tests/load/k6/stage1_baseline.js

echo "Load test completed. Preserve the JSON result with the environment metadata for capacity analysis."
