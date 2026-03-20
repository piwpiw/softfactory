#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="$PROJECT_ROOT/.n8n/database.sqlite"
BACKUP_DIR="$PROJECT_ROOT/n8n/backups/database"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ ! -f "$DB_PATH" ]; then
  echo "database not found: $DB_PATH"
  exit 1
fi

cp "$DB_PATH" "$BACKUP_DIR/database_$STAMP.sqlite"
echo "database backup complete: $BACKUP_DIR/database_$STAMP.sqlite"
