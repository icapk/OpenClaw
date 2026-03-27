#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
INTERVAL="${1:-60}"

bash "$BASE_DIR/init.sh"
python3 "$BASE_DIR/scripts/workflow.py" daemon --interval "$INTERVAL"
