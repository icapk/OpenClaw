# Custom UI: Board（嵌入官方18789页面）

目标：
- 看板显示在 OpenClaw 官方控制台（18789）原生侧边栏内
- `/chat` 仅聊天，`/board` 仅看板（兼容旧链接 `/chat?panel=board` 自动跳转）
- 看板任务数据主链路来自 `tasks/in_progress/` 实时聚合（禁止静态快照作为主链路）
- 自研代码与官方 dist 解耦，升级后可一键恢复

## 目录
- `src/loader.js`：注入侧边栏“看板”入口 + 在 `/board` 渲染看板 + 兼容旧链接跳转
- `src/generate-dashboard.js`：从 `tasks/in_progress/` 聚合实时任务数据，生成 `data/dashboard.json`
- `data/dashboard.json`：聚合产物（每次重挂/门禁前重生成）
- `../../scripts/reapply-custom-ui.sh`：升级后重挂脚本（内置数据重生成）
- `../../scripts/board-release-gate.sh`：发布门禁（5项断言）

## 升级后恢复
```bash
bash /Users/a1/.openclaw/workspace/scripts/reapply-custom-ui.sh
```
然后浏览器强刷 `Cmd+Shift+R`。

## 发布前门禁
```bash
bash /Users/a1/.openclaw/workspace/scripts/board-release-gate.sh
```

## 约束
- 不直接长期维护官方 dist 业务代码
- dist 内仅保留最小 loader 挂载点
- 业务逻辑统一维护在 workspace/custom-ui 下
