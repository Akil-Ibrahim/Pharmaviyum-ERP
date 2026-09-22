#!/usr/bin/env bash
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_S3_URI:?BACKUP_S3_URI is required, e.g. s3://bucket/pharmaviyum/postgres}"
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
: "${AWS_DEFAULT_REGION:?AWS_DEFAULT_REGION is required}"

command -v pg_dump >/dev/null || { echo "pg_dump is required" >&2; exit 1; }
command -v aws >/dev/null || { echo "aws CLI is required" >&2; exit 1; }

BACKUP_DIR="${BACKUP_DIR:-/tmp/pharmaviyum-backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="${BACKUP_DIR}/pharmaviyum_${TIMESTAMP}.dump"
REMOTE_FILE="${BACKUP_S3_URI%/}/pharmaviyum_${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"
trap 'rm -f "$BACKUP_FILE"' EXIT

echo "Creating PostgreSQL custom-format backup: $BACKUP_FILE"
pg_dump --dbname="$DATABASE_URL" --format=custom --no-owner --no-privileges --file="$BACKUP_FILE"

echo "Uploading backup: $REMOTE_FILE"
AWS_ARGS=(s3 cp "$BACKUP_FILE" "$REMOTE_FILE" --sse AES256)
if [[ -n "${AWS_S3_ENDPOINT_URL:-}" ]]; then
  AWS_ARGS+=(--endpoint-url "$AWS_S3_ENDPOINT_URL")
fi
aws "${AWS_ARGS[@]}"

echo "Backup completed successfully."
echo "Remote backup: $REMOTE_FILE"
