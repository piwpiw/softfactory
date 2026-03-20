#!/bin/bash
# Compatibility wrapper. Canonical script lives under scripts/.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/scripts/deploy-verify.sh" "$@"
