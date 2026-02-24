#!/usr/bin/env bash
# Database backup script with 7-day rotation.
# Usage: ./scripts/backup-db.sh
# Can be run from cron or as a Docker one-shot service.
#
# Required env vars (or defaults):
#   PGHOST, PGPORT, PGUSER, PGDATABASE, PGPASSWORD
#   BACKUP_DIR (default: /backups)
#   RETENTION_DAYS (default: 7)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
PGHOST="${PGHOST:-postgres}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-reconforge}"
PGDATABASE="${PGDATABASE:-reconforge}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${PGDATABASE}_${TIMESTAMP}.sql.gz"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

mkdir -p "${BACKUP_DIR}"

echo "[$(date -Iseconds)] Starting backup of ${PGDATABASE}..."

pg_dump -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" \
  --no-owner --no-acl --format=plain | gzip > "${FILEPATH}"

SIZE=$(du -h "${FILEPATH}" | cut -f1)
echo "[$(date -Iseconds)] Backup complete: ${FILEPATH} (${SIZE})"

# Rotation: delete backups older than RETENTION_DAYS
DELETED=$(find "${BACKUP_DIR}" -name "${PGDATABASE}_*.sql.gz" -mtime "+${RETENTION_DAYS}" -print -delete | wc -l)
if [ "${DELETED}" -gt 0 ]; then
  echo "[$(date -Iseconds)] Rotated ${DELETED} old backup(s)"
fi

echo "[$(date -Iseconds)] Done. Current backups:"
ls -lh "${BACKUP_DIR}/${PGDATABASE}_"*.sql.gz 2>/dev/null || echo "  (none)"
