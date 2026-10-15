#!/usr/bin/env bash
set -euo pipefail

# Guarded k6 runner. Use local development or an isolated staging environment
# populated exclusively with synthetic data. Production-like targets are rejected.

BASE_URL="${BASE_URL:-http://localhost:8000}"
OUTPUT_DIR="${LOAD_TEST_OUTPUT_DIR:-artifacts/load-tests}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FILE="${OUTPUT_DIR}/pharmaviyum-erp-${TIMESTAMP}.json"

case "${BASE_URL,,}" in
  *prod*|*production*|*live*|*pharmaviyum.onrender.com*|*pharmaviyum-api.onrender.com*)
    echo "Refusing to run load tests against a known or production-like target: ${BASE_URL}" >&2
    exit 2
    ;;
esac

if [[ "${BASE_URL}" == http://localhost* || "${BASE_URL}" == http://127.0.0.1* || "${BASE_URL}" == http://0.0.0.0* ]]; then
  :
elif [[ "${ALLOW_REMOTE_TARGET:-false}" != "true" || "${LOAD_TEST_ENV:-}" != "staging" ]]; then
  echo "Remote targets require ALLOW_REMOTE_TARGET=true and LOAD_TEST_ENV=staging." >&2
  echo "Use an isolated staging deployment and synthetic data only." >&2
  exit 2
fi

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "AUTH_TOKEN is required for a dedicated synthetic test account." >&2
  exit 2
fi
if [[ ! "${PHARMACY_ID:-}" =~ ^[1-9][0-9]*$ ]]; then
  echo "PHARMACY_ID must be the ID of a pharmacy accessible to AUTH_TOKEN." >&2
  exit 2
fi
if [[ "${ENABLE_AI:-false}" == "true" && -z "${AI_QUERY:-}" ]]; then
  echo "AI is enabled. Set AI_QUERY to a deterministic, non-patient-specific prompt." >&2
  exit 2
fi

if [[ "${ENABLE_WRITES:-false}" == "true" ]]; then
  if [[ "${CONFIRM_SYNTHETIC_WRITES:-}" != "YES" ]]; then
    echo "Writes are disabled by default. Set CONFIRM_SYNTHETIC_WRITES=YES only for disposable staging data." >&2
    exit 2
  fi
  if [[ -z "${SUPERUSER_TOKEN:-}" ]]; then
    echo "ENABLE_WRITES=true requires a dedicated staging SUPERUSER_TOKEN." >&2
    exit 2
  fi
  if [[ ! "${PRODUCT_ID:-}" =~ ^[1-9][0-9]*$ ]]; then
    echo "ENABLE_WRITES=true requires PRODUCT_ID for an existing synthetic product." >&2
    exit 2
  fi
  if [[ ! "${WRITE_VUS:-2}" =~ ^([1-9]|1[0-9]|20)$ ]]; then
    echo "WRITE_VUS must be an integer from 1 to 20." >&2
    exit 2
  fi
  echo "Synthetic inventory create/delete transaction workload is enabled."
fi

command -v k6 >/dev/null 2>&1 || {
  echo "k6 is required but was not found in PATH." >&2
  exit 127
}

mkdir -p "${OUTPUT_DIR}"

if [[ -n "${SUPERUSER_TOKEN:-}" ]]; then
  echo "Privileged pharmacy-admin read workload is enabled."
fi
if [[ "${ENABLE_AI:-false}" == "true" ]]; then
  echo "Mortarium AI workload is enabled; confirm provider/API cost limits before running."
fi

echo "Running Pharmaviyum ERP/CRM load test against ${BASE_URL}"
echo "Read workload peak VUs: ${PEAK_VUS:-20}"
echo "JSON output: ${OUTPUT_FILE}"
k6 run --out "json=${OUTPUT_FILE}" tests/load/k6/stage1_baseline.js

echo "Load test completed. Preserve the JSON result with environment and deployment metadata."
echo "Completion alone is not a pass: review thresholds, failed checks, DB/Redis and container metrics."
