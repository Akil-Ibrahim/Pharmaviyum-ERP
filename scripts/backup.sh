#!/bin/bash
set -e

echo "💾 Creating database backup..."

# Create backup directory
mkdir -p backups/postgres

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U ${DB_USER} ${DB_NAME} | \
    gzip > backups/postgres/backup_${TIMESTAMP}.sql.gz

echo "✅ Backup created: backups/postgres/backup_${TIMESTAMP}.sql.gz"

# Keep only last 7 days of backups
echo "🧹 Cleaning old backups..."
find backups/postgres -name "backup_*.sql.gz" -mtime +7 -delete

echo "✅ Backup complete!"
