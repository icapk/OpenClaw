# 看板P0重构与真实任务源改造｜验收报告

- 时间：2026-03-17 06:58 (GMT+8)
- 结论：**完成**

## 变更文件清单（本次执行产物）
1. `custom-ui/board/data/dashboard.json`（由实时聚合脚本重生成）
2. `output/reports/board-p0-gate-20260317-0656.log`（发布门禁完整日志）
3. `output/reports/board-p0-remake-report-20260317-0658.md`（本报告）

> 说明：路由隔离、互斥高亮、真实数据主链路实现代码已存在于：
> - `custom-ui/board/src/loader.js`
> - `custom-ui/board/src/generate-dashboard.js`
> - `scripts/board-release-gate.sh`

## 关键命令与输出

### 1) 发布门禁执行
```bash
bash /Users/a1/.openclaw/workspace/scripts/board-release-gate.sh
```

关键输出：
- `[gate] 3/5 assert route isolation (/board + legacy redirect + /chat)` → `OK route isolation checks`
- `[gate] 4/5 assert mutual active state` → `OK mutual-active checks`
- `[gate] 5/5 assert refresh stability` → `OK refresh stable (counts unchanged), pm=1 tester=1 ...`
- `[gate] PASS all 5 assertions`

### 2) 证据日志落盘
```bash
bash /Users/a1/.openclaw/workspace/scripts/board-release-gate.sh | tee /Users/a1/.openclaw/workspace/output/reports/board-p0-gate-20260317-0656.log
```

关键输出：
- `[board-data] PM todoCount=1`
- `[board-data] Tester todoCount=1`
- `[gate] PASS all 5 assertions`

## 硬性要求逐项对照
1. 路由隔离（`/chat`仅聊天，`/board`仅看板，兼容旧链接）
   - 证据：`loader.js` 含 `const BOARD_URL = '/board'`、`isLegacyBoardUrl()`、`location.replace('/board')`。
   - 门禁：`[gate] 3/5 ... OK route isolation checks`

2. 真实数据主链路（来自 `tasks/in_progress/` 实时聚合）
   - 证据：`generate-dashboard.js` 读取 `TASK_DIR=tasks/in_progress`，并写入 `source: 'tasks/in_progress realtime aggregation'`。
   - 门禁：`[gate] 1/5 generate realtime board data` + `[gate] 5/5 ... OK source/summary schema`

3. 聊天/看板选中态互斥
   - 证据：`loader.js` 中 `chatLink.removeAttribute('aria-current')`、`boardLink.setAttribute('aria-current','page')`、`data-oc-board-mode`/`data-oc-chat-mode`。
   - 门禁：`[gate] 4/5 ... OK mutual-active checks`

4. 发布门禁结果（隔离、互斥、数据一致、刷新稳定）
   - 证据：门禁日志完整记录在 `board-p0-gate-20260317-0656.log`。
   - 结果：`PASS all 5 assertions`

## 证据路径（workspace内可读）
- `/Users/a1/.openclaw/workspace/output/reports/board-p0-gate-20260317-0656.log`
- `/Users/a1/.openclaw/workspace/custom-ui/board/src/loader.js`
- `/Users/a1/.openclaw/workspace/custom-ui/board/src/generate-dashboard.js`
- `/Users/a1/.openclaw/workspace/scripts/board-release-gate.sh`
- `/Users/a1/.openclaw/workspace/custom-ui/board/data/dashboard.json`
