#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
TARGET="$PROJECT_ROOT/n8n/backups/full_$STAMP"
mkdir -p "$TARGET"

bash "$PROJECT_ROOT/scripts/n8n-backup-workflows.sh"
bash "$PROJECT_ROOT/scripts/n8n-backup-database.sh"
cp -r "$PROJECT_ROOT/n8n/workflows" "$TARGET/workflows"
cp "$PROJECT_ROOT/.n8nconfig.json" "$TARGET/.n8nconfig.json"

echo "full backup complete: $TARGET"
