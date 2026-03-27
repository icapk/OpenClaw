# 看板P0再次打回修复报告（2026-03-17 07:05）

## 修复结论
- 已修复 3 项未通过项：
  1. `/board` 现保持为仅看板，不再落入 `/board/chat?session=main`
  2. 聊天/看板 active 状态严格互斥（class 与 aria-current 同步）
  3. 刷新/切换后不会回退聊天链路（新增路由规范化）

## 变更文件
- `custom-ui/board/src/loader.js`

## 关键命令输出（摘录）
```bash
$ bash scripts/board-release-gate.sh
[gate] 3/5 assert route isolation (/board + legacy redirect + /chat)
OK route isolation checks
[gate] 4/5 assert mutual active state
OK mutual-active checks
[gate] PASS all 5 assertions
```

```bash
$ bash scripts/reapply-custom-ui.sh
[OK] 已重挂自定义看板入口到 18789 官方页面
```

浏览器实测（evaluate）：
```json
{"url":"http://127.0.0.1:18789/chat?session=main","chat":{"cls":"nav-item active","aria":"page"},"board":{"href":"/board","cls":"nav-item","aria":null,"active":"0"}}
```

点击看板后：
```json
{"url":"http://127.0.0.1:18789/board","path":"/board","title":"看板"}
```

## 证据路径
- `custom-ui/board/src/loader.js`
- `scripts/board-release-gate.sh`
- `scripts/reapply-custom-ui.sh`
- `output/reports/board-remake-fix-20260317-0705.md`
