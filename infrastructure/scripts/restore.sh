#!/usr/bin/env bash
# restore.sh — Restores a pg_dump backup created by backup.sh.
# Usage:
#   ./infrastructure/scripts/restore.sh ./backups/swiftsale_20260515_120000.sql.gz

set -euo pipefail

BACKUP_FILE="${1:-}"

if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: $0 <backup_file.sql.gz>"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Error: file not found: $BACKUP_FILE"
  exit 1
fi

DB_NAME="${DB_NAME:-swiftsale}"
DB_USER="${DB_USER:-swiftsale}"

echo "[restore] Restoring '${DB_NAME}' from ${BACKUP_FILE}..."
echo "[restore] WARNING: This will drop and recreate all tables."
read -r -p "Continue? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
  echo "[restore] Aborted."
  exit 0
fi

gunzip -c "$BACKUP_FILE" | psql \
  --host="${DB_HOST:-localhost}" \
  --port="${DB_PORT:-5432}" \
  --username="${DB_USER}" \
  "${DB_NAME}"

echo "[restore] Done."
