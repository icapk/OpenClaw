# Custom UI: Board (嵌入官方18789页面)

目标：
- 看板显示在 OpenClaw 官方控制台（18789）原生侧边栏内
- 自研代码与官方 dist 解耦
- 升级官方版本后可一键恢复

## 目录
- `src/loader.js`：注入侧边栏“看板”入口 + 在 `/chat?panel=board` 渲染看板
- `data/dashboard.json`：看板数据源（当前快照）
- `../../scripts/reapply-custom-ui.sh`：升级后重挂脚本

## 升级后恢复
```bash
bash /Users/a1/.openclaw/workspace/scripts/reapply-custom-ui.sh
```
然后浏览器强刷 `Cmd+Shift+R`。

## 约束
- 不直接长期维护官方 dist 业务代码
- dist 内仅保留最小 loader 挂载点
- 业务逻辑统一维护在 workspace/custom-ui 下
