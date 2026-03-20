#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs/n8n"
ARCHIVE_DIR="$LOG_DIR/archive"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

if [ -d "$LOG_DIR" ]; then
  find "$LOG_DIR" -maxdepth 1 -type f -name "*.log" -exec gzip -c {} \; > "$ARCHIVE_DIR/n8n_logs_$STAMP.gz" || true
  find "$ARCHIVE_DIR" -type f -mtime +30 -delete || true
fi

echo "log rotation complete: $ARCHIVE_DIR"
