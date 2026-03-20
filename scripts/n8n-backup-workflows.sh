#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/n8n/backups/workflows"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if ! command -v n8n >/dev/null 2>&1; then
  echo "n8n command not found"
  exit 1
fi

n8n export:workflow --all --separate --output "$BACKUP_DIR/$STAMP"
echo "workflow backup complete: $BACKUP_DIR/$STAMP"
