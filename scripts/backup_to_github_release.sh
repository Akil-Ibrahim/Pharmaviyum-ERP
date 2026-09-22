#!/usr/bin/env bash
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${GITHUB_BACKUP_TOKEN:?GITHUB_BACKUP_TOKEN is required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is required, e.g. ibrahimengpy/Pharmaviyum-CRM}"

command -v pg_dump >/dev/null || { echo "pg_dump is required" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v openssl >/dev/null || { echo "openssl is required" >&2; exit 1; }

BACKUP_DIR="${BACKUP_DIR:-/tmp/pharmaviyum-backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="${BACKUP_DIR}/pharmaviyum_${TIMESTAMP}.dump"
UPLOAD_FILE="${BACKUP_FILE}.enc"
TAG="db-backup-${TIMESTAMP}"
RELEASE_NAME="Database backup ${TIMESTAMP}"
API="https://api.github.com/repos/${GITHUB_REPOSITORY}"

mkdir -p "$BACKUP_DIR"
trap 'rm -f "$BACKUP_FILE" "$UPLOAD_FILE"' EXIT

echo "Creating PostgreSQL custom-format backup."
pg_dump --dbname="$DATABASE_URL" --format=custom --no-owner --no-privileges --file="$BACKUP_FILE"

if [[ ! -s "$BACKUP_FILE" ]]; then
  echo "Backup file is empty." >&2
  exit 1
fi

: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY is required}"
echo "Encrypting backup."
openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_ENCRYPTION_KEY \
  -in "$BACKUP_FILE" -out "$UPLOAD_FILE"

SIZE="$(stat -c%s "$UPLOAD_FILE")"
if (( SIZE >= 2147483648 )); then
  echo "Encrypted backup is too large for a GitHub release asset (2 GiB maximum)." >&2
  exit 1
fi

AUTH=(-H "Accept: application/vnd.github+json" -H "Authorization: Bearer $GITHUB_BACKUP_TOKEN" -H "X-GitHub-Api-Version: 2026-03-10")

echo "Creating GitHub Release $TAG."
RELEASE_JSON="$(curl -fsSL -X POST "$API/releases" "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  --data "$(printf '{"tag_name":"%s","target_commitish":"main","name":"%s","body":"Automated encrypted PostgreSQL backup.","draft":false,"prerelease":true}' "$TAG" "$RELEASE_NAME")")"

RELEASE_ID="$(printf '%s' "$RELEASE_JSON" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

echo "Uploading encrypted backup asset."
curl -fsSL -X POST "https://uploads.github.com/repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}/assets?name=pharmaviyum_${TIMESTAMP}.dump.enc" \
  "${AUTH[@]}" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@$UPLOAD_FILE" >/dev/null

echo "Backup completed successfully."
echo "Release tag: $TAG"
echo "Release asset: pharmaviyum_${TIMESTAMP}.dump.enc"
