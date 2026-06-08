#!/usr/bin/env bash
set -euo pipefail

# Root launcher for development mode.
# Delegates to scripts/run_dev.sh to keep a single source of truth.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/scripts/run_dev.sh"
