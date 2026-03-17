#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_UI_DIR="/opt/homebrew/lib/node_modules/openclaw/dist/control-ui"
WORKSPACE="/Users/a1/.openclaw/workspace"
CUSTOM_DIR="$WORKSPACE/custom-ui/board"
LOADER_SRC="$CUSTOM_DIR/src/loader.js"
GENERATOR_SRC="$CUSTOM_DIR/src/generate-dashboard.js"
DATA_SRC="$CUSTOM_DIR/data/dashboard.json"

if [[ ! -d "$OPENCLAW_UI_DIR" ]]; then
  echo "[ERR] 未找到 OpenClaw UI 目录: $OPENCLAW_UI_DIR"
  exit 1
fi

if [[ ! -f "$LOADER_SRC" ]]; then
  echo "[ERR] 未找到自定义 loader: $LOADER_SRC"
  exit 1
fi
if [[ ! -f "$GENERATOR_SRC" ]]; then
  echo "[ERR] 未找到数据生成器: $GENERATOR_SRC"
  exit 1
fi

# 每次重挂前都从 tasks/in_progress 重新聚合，避免静态快照成为主链路
node "$GENERATOR_SRC"

mkdir -p "$OPENCLAW_UI_DIR/assets" "$OPENCLAW_UI_DIR/office/data"
cp "$LOADER_SRC" "$OPENCLAW_UI_DIR/assets/custom-sidebar-link.js"

if [[ -f "$DATA_SRC" ]]; then
  cp "$DATA_SRC" "$OPENCLAW_UI_DIR/office/data/dashboard.json"
fi

INDEX_HTML="$OPENCLAW_UI_DIR/index.html"
python3 - <<'PY'
from pathlib import Path
p = Path('/opt/homebrew/lib/node_modules/openclaw/dist/control-ui/index.html')
s = p.read_text(encoding='utf-8')
legacy = '    <script defer src="./assets/custom-sidebar-link.js"></script>\n'
head_inject = '    <script src="./assets/custom-sidebar-link.js"></script>\n'
module_marker = '    <script type="module" crossorigin src="./assets/index-Qb3PJV7U.js"></script>\n'

if legacy in s:
    s = s.replace(legacy, '')
if head_inject not in s:
    if module_marker in s:
        s = s.replace(module_marker, head_inject + module_marker)
    else:
        s = s.replace('</head>', head_inject + '  </head>')

p.write_text(s, encoding='utf-8')
PY

echo "[OK] 已重挂自定义看板入口到 18789 官方页面"
echo "[TIP] 请浏览器强刷 Cmd+Shift+R"
