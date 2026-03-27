#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

cp -n "$BASE_DIR/config/config.template.json" "$BASE_DIR/config/config.json" || true
mkdir -p "$BASE_DIR/output/drafts" "$BASE_DIR/output/published" "$BASE_DIR/output/reports" "$BASE_DIR/output/logs"
mkdir -p "/Users/a1/.openclaw/workspace/output/content_ops_mvp"/{drafts,published,reports,logs}
mkdir -p "/Users/a1/.openclaw/workspace/output/reports"

python3 "$BASE_DIR/scripts/workflow.py" init

echo "初始化完成: $BASE_DIR"
