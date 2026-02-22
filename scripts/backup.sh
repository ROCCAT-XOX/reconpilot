#!/usr/bin/env bash
# ReconForge Database Backup Script
# Called by Celery Beat daily at 02:00 UTC
# Can also be run manually: bash scripts/backup.sh

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/app/data/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/reconforge_${TIMESTAMP}.sql.gz"

# Parse DATABASE_URL to extract connection params
# Expected format: postgresql+asyncpg://user:pass@host:port/dbname
DB_URL="${DATABASE_URL:-}"
if [ -z "$DB_URL" ]; then
    echo "ERROR: DATABASE_URL not set" >&2
    exit 1
fi

# Strip the driver prefix (postgresql+asyncpg:// -> user:pass@host:port/dbname)
DB_CONN="${DB_URL#*://}"
DB_USER="${DB_CONN%%:*}"
DB_REMAINING="${DB_CONN#*:}"
DB_PASS="${DB_REMAINING%%@*}"
DB_REMAINING="${DB_REMAINING#*@}"
DB_HOST="${DB_REMAINING%%:*}"
DB_REMAINING="${DB_REMAINING#*:}"
DB_PORT="${DB_REMAINING%%/*}"
DB_NAME="${DB_REMAINING#*/}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting backup: ${DB_NAME}@${DB_HOST}:${DB_PORT} -> ${BACKUP_FILE}"

# Run pg_dump
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    --format=custom \
    | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup completed: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Cleanup old backups
DELETED=$(find "$BACKUP_DIR" -name "reconforge_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "Cleaned up ${DELETED} backups older than ${RETENTION_DAYS} days"
fi

echo "Backup successful"
