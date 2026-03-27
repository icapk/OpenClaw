#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

bash "$BASE_DIR/init.sh"
python3 "$BASE_DIR/scripts/workflow.py" run_once
