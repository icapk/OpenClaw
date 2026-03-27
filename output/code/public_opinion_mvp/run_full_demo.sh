#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

mkdir -p output/{alerts,timeline,briefs,reports,notifications,events,dashboard,health} web/data

python3 scripts/workflow.py --root "$ROOT"
cp output/dashboard/dashboard_data.json web/data/dashboard_data.json

# 新增：自动执行验收并产出报告
./run_acceptance.sh

PORT=${PORT:-8099}
if command -v lsof >/dev/null 2>&1 && lsof -i :"$PORT" >/dev/null 2>&1; then
  echo "[dashboard] port $PORT already in use, skip start"
else
  nohup python3 -m http.server "$PORT" --directory web > output/dashboard/server.log 2>&1 &
  echo $! > output/dashboard/server.pid
  echo "[dashboard] started pid=$(cat output/dashboard/server.pid)"
fi

echo "\n=== FULL DEMO DONE (v1.0) ==="
echo "采集: output/raw_items.json"
echo "告警: output/alerts/events_alerts.json"
echo "时间线: output/timeline/events_timeline.json"
echo "快报: output/briefs/event_brief_5w1h.md"
echo "复盘: output/reports/retro_24h.md"
echo "周报: output/reports/weekly_summary.md"
echo "通知日志: output/notifications/message_simulated.log"
echo "飞书适配日志: output/notifications/feishu_doc_adapter.log"
echo "Dashboard数据: output/dashboard/dashboard_data.json"
echo "验收报告: output/reports/验收报告.md"
echo "最终清单: output/reports/最终功能清单_v1.0.md"
echo "Dashboard: http://127.0.0.1:${PORT}"
