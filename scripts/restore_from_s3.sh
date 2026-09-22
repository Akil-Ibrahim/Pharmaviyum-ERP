#!/usr/bin/env bash
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${GITHUB_BACKUP_TOKEN:?GITHUB_BACKUP_TOKEN is required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is required, e.g. ibrahimengpy/Pharmaviyum-CRM}"
: "${BACKUP_TAG:?BACKUP_TAG is required, e.g. db-backup-20260922T020000Z}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY is required}"

if [[ "${ALLOW_DESTRUCTIVE_RESTORE:-false}" != "true" ]]; then
  echo "Refusing destructive restore. Set ALLOW_DESTRUCTIVE_RESTORE=true explicitly." >&2
  exit 2
fi

command -v pg_restore >/dev/null || { echo "pg_restore is required" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v openssl >/dev/null || { echo "openssl is required" >&2; exit 1; }

BACKUP_DIR="${BACKUP_DIR:-/tmp/pharmaviyum-backups}"
mkdir -p "$BACKUP_DIR"
trap 'rm -f "$BACKUP_DIR"/backup.dump.enc "$BACKUP_DIR"/backup.dump' EXIT

API="https://api.github.com/repos/${GITHUB_REPOSITORY}"
AUTH=(-H "Accept: application/vnd.github+json" -H "Authorization: Bearer $GITHUB_BACKUP_TOKEN" -H "X-GitHub-Api-Version: 2026-03-10")

echo "Locating release $BACKUP_TAG."
RELEASE_JSON="$(curl -fsSL "$API/releases/tags/$BACKUP_TAG" "${AUTH[@]}")"
ASSET_URL="$(printf '%s' "$RELEASE_JSON" | python -c 'import json,sys; d=json.load(sys.stdin); a=[x for x in d["assets"] if x["name"].endswith(".dump.enc")]; print(a[0]["url"] if a else (_ for _ in ()).throw(SystemExit("Encrypted backup asset not found")))')"

echo "Downloading encrypted backup."
curl -fsSL "$ASSET_URL" "${AUTH[@]}" -H "Accept: application/octet-stream" -o "$BACKUP_DIR/backup.dump.enc"

echo "Decrypting backup."
openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_KEY \
  -in "$BACKUP_DIR/backup.dump.enc" -out "$BACKUP_DIR/backup.dump"

echo "Restoring into target database."
pg_restore --dbname="$DATABASE_URL" --format=custom --clean --if-exists --no-owner --no-privileges "$BACKUP_DIR/backup.dump"

echo "Restore completed successfully."
