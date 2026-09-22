#!/usr/bin/env bash
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_S3_URI:?BACKUP_S3_URI is required}"
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
: "${AWS_DEFAULT_REGION:?AWS_DEFAULT_REGION is required}"
: "${BACKUP_OBJECT:?BACKUP_OBJECT is required, e.g. pharmaviyum_20260922T020000Z.dump}"

if [[ "${ALLOW_DESTRUCTIVE_RESTORE:-false}" != "true" ]]; then
  echo "Refusing destructive restore. Set ALLOW_DESTRUCTIVE_RESTORE=true explicitly." >&2
  exit 2
fi

command -v pg_restore >/dev/null || { echo "pg_restore is required" >&2; exit 1; }
command -v aws >/dev/null || { echo "aws CLI is required" >&2; exit 1; }

BACKUP_DIR="${BACKUP_DIR:-/tmp/pharmaviyum-backups}"
BACKUP_FILE="${BACKUP_DIR}/$(basename "$BACKUP_OBJECT")"
mkdir -p "$BACKUP_DIR"
trap 'rm -f "$BACKUP_FILE"' EXIT

REMOTE_FILE="${BACKUP_S3_URI%/}/${BACKUP_OBJECT}"
echo "Downloading backup: $REMOTE_FILE"

AWS_ARGS=(s3 cp "$REMOTE_FILE" "$BACKUP_FILE")
if [[ -n "${AWS_S3_ENDPOINT_URL:-}" ]]; then
  AWS_ARGS+=(--endpoint-url "$AWS_S3_ENDPOINT_URL")
fi
aws "${AWS_ARGS[@]}"

echo "Restoring into target database."
pg_restore --dbname="$DATABASE_URL" --format=custom --clean --if-exists --no-owner --no-privileges "$BACKUP_FILE"

echo "Restore completed successfully."
