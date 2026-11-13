#!/bin/bash
# Automated Database Backup with Rotation
set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pharmaviyum_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "$BACKUP_DIR"
echo "Creating backup: $BACKUP_FILE"

docker compose exec -T db pg_dump -U postgres pharmaviyum | gzip > "$BACKUP_FILE"
find "$BACKUP_DIR" -name "pharmaviyum_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup complete: $BACKUP_FILE"
