#!/usr/bin/env bash
# backup.sh — Creates a timestamped pg_dump of the SwiftSale database.
# Usage (from project root):
#   ./infrastructure/scripts/backup.sh
# Or inside Docker:
#   docker compose exec postgres /bin/sh -c "..."

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_NAME="${DB_NAME:-swiftsale}"
DB_USER="${DB_USER:-swiftsale}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[backup] Starting backup of database '${DB_NAME}' → ${FILENAME}"

pg_dump \
  --host="${DB_HOST:-localhost}" \
  --port="${DB_PORT:-5432}" \
  --username="${DB_USER}" \
  --format=plain \
  --no-owner \
  --no-acl \
  "${DB_NAME}" | gzip > "${FILENAME}"

echo "[backup] Done: ${FILENAME} ($(du -sh "${FILENAME}" | cut -f1))"

# Retain only the last 30 backups
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -type f | sort | head -n -30 | xargs -r rm --
echo "[backup] Old backups pruned (kept last 30)."
