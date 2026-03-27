#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

mkdir -p output/reports

python3 - <<'PY'
import json
from pathlib import Path

root = Path('.').resolve()
checks = []

def loadj(p):
    return json.loads((root / p).read_text(encoding='utf-8'))

def exists(p):
    return (root / p).exists()

def add(name, ok, detail):
    checks.append((name, ok, detail))

# 1 聚类优化 + 对比指标
try:
    timeline = loadj('output/timeline/events_timeline.json')
    frag = timeline.get('fragmentation_optimization', {})
    before = frag.get('before', {})
    after = frag.get('after', {})
    ok = bool(before.get('event_count') is not None and after.get('event_count') is not None)
    add('1) 聚类优化与指标输出', ok, f"before={before}, after={after}")
except Exception as e:
    add('1) 聚类优化与指标输出', False, str(e))

# 2 采集鲁棒性
try:
    raw = loadj('output/raw_items.json')
    meta = raw.get('meta', {})
    pol = meta.get('fetch_policy', {})
    ok = ('retries' in pol and 'timeout_sec' in pol and 'fallback_to_sample' in pol)
    add('2) 采集重试/超时/fallback', ok, f"fetch_policy={pol}, fallback_records={len(meta.get('fallback_records', []))}")
except Exception as e:
    add('2) 采集重试/超时/fallback', False, str(e))

# 3 通知链路
try:
    log = (root / 'output/notifications/message_simulated.log').read_text(encoding='utf-8')
    ok = ('result=' in log) and ('degraded_to_mock' in log or 'sent' in log or 'mock' in log)
    add('3) notifier 实发可切换+降级', ok, log.strip()[:200])
except Exception as e:
    add('3) notifier 实发可切换+降级', False, str(e))

# 4 feishu_doc 适配
try:
    flog = (root / 'output/notifications/feishu_doc_adapter.log').read_text(encoding='utf-8')
    ok = ('mode=' in flog and ('status=real_sent' in flog or 'status=mock_fallback' in flog or 'status=mock_only' in flog))
    add('4) feishu_doc mock/real 切换+容错', ok, flog.strip()[:240])
except Exception as e:
    add('4) feishu_doc mock/real 切换+容错', False, str(e))

# 5 dashboard 增强
try:
    dash = loadj('output/dashboard/dashboard_data.json')
    trend_ok = len(dash.get('trend_series', [])) > 0
    frag_ok = bool(dash.get('fragmentation_optimization', {}).get('before'))
    add('5) Dashboard 趋势图+碎片化对比', trend_ok and frag_ok, f"trend_points={len(dash.get('trend_series', []))}, has_frag={frag_ok}")
except Exception as e:
    add('5) Dashboard 趋势图+碎片化对比', False, str(e))

# 6 脚本完备
ok6 = exists('run_full_demo.sh') and exists('run_acceptance.sh')
add('6) 完整脚本 run_full_demo + run_acceptance', ok6, '脚本存在性检查')

# 7 文档与清单
ok7 = exists('README.md') and exists('output/reports/最终功能清单_v1.0.md')
add('7) README 完整版 + 最终清单 v1.0', ok7, '文档存在性检查')

all_ok = all(x[1] for x in checks)
lines = ['# 验收报告', '']
for name, ok, detail in checks:
    lines.append(f"- {'✅' if ok else '❌'} {name}")
    lines.append(f"  - {detail}")
lines.append('')
lines.append(f"## 结论\n{'✅ 全部通过' if all_ok else '❌ 存在失败项，需补救'}")

out = root / 'output/reports/验收报告.md'
out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f"[acceptance] report -> {out}")
print(f"[acceptance] all_ok={all_ok}")
PY
