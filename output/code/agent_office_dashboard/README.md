# 老板视角子Agent可视化看板（办公室风格）

这是一个可本地运行的 MVP，看板按“办公室”布局展示子 Agent 运行状态。

## 功能覆盖

- ✅ 展示所有子 agent 状态：`active/done`（在线/离线）
- ✅ 展示当前任务、待办数量、最近完成任务、耗时、token 消耗
- ✅ 办公室布局：
  - 老板办公室（总览卡）
  - HR/研发/运营工位卡片（点击查看详情）
  - 大厅任务看板（待办/进行中/完成）
- ✅ 支持待办任务：读取 `data/todo.json`
- ✅ 一键刷新：页面按钮触发 `/api/refresh`，调用 `generate_data.py` 重新生成 `data/dashboard.json`

---

## 目录结构

```text
output/code/agent_office_dashboard/
├── README.md
├── index.html            # Portal 首页（含“办公室”按钮）
├── generate_data.py
├── serve.py
├── run.sh
├── data/
│   ├── todo.json
│   └── dashboard.json   # 运行后生成
└── web/
    ├── index.html
    ├── style.css
    └── app.js
```

---

## 一条命令启动

在项目根目录执行：

```bash
cd output/code/agent_office_dashboard
./run.sh
```

启动后访问：

- Portal 首页：`http://127.0.0.1:18979`
- 办公室看板：`http://127.0.0.1:18979/office`

---

## “办公室”按钮入口（新增硬要求）

### 当前实现（无主站时）

已创建 Portal 首页 `index.html`，含亮色按钮：

- 按钮名称：`🏢 办公室`
- 按钮位置：Portal 首页主卡片中部（标题下方）
- 跳转路径：`/office`

### 若已有主站，可直接合并的按钮片段

```html
<a class="office-btn" href="/office">🏢 办公室</a>
```

建议样式（亮色）：

```css
.office-btn {
  display:inline-block;
  padding:12px 22px;
  background:#ffd54f;
  color:#1f2937;
  font-weight:700;
  border-radius:10px;
  text-decoration:none;
  border:2px solid #ffca28;
}
```

路由说明：将 `/office` 路由到 `web/index.html`（办公室看板页面）。

---

## 数据来源说明

`generate_data.py` 数据采集优先级：

1. 尝试读取 OpenClaw CLI 输出（兼容多种命令）：
   - `openclaw subagents list --json`
   - `openclaw subagents list`
   - `openclaw sessions list --json`
   - `openclaw sessions list`
2. 若 CLI 不可用，则读取本地快照：
   - `data/subagents_snapshot.json`（可选）
3. 若仍无数据，则使用内置示例数据兜底（保证页面可展示）

`todo.json` 始终会被合并进大厅任务看板。

---

## 如何扩展为真实数据源

你可以在 `generate_data.py` 中替换 `collect_subagents_raw()`：

1. 对接 OpenClaw 更稳定的 JSON 接口（若未来有官方 endpoint）
2. 从你自己的任务系统读取（如本地 DB、API、消息队列）
3. 增加字段映射（比如 cost、模型名、错误率、重试次数）
4. 在 `agents[].tasks` 中保留更长历史，前端即可展示完整任务流水

前端无需改动太多，只要继续输出到 `data/dashboard.json` 即可。

---

## 已知限制（MVP）

1. OpenClaw CLI 不同版本输出格式可能不同，当前脚本做了兼容解析但不保证覆盖所有格式。
2. 刷新是“手动按钮触发”，不是实时流式订阅。
3. 部门字段若源数据缺失，会按 HR/研发/运营做兜底分配。
4. token 与耗时依赖上游数据是否提供；缺失时为 0。

---

## 快速验收

1. 执行 `./run.sh`
2. 打开 `http://127.0.0.1:18979`（点击亮色“🏢 办公室”按钮）
3. 检查：
   - 顶部总览卡有 agent 数、token、耗时
   - 工位卡片可点击查看详情（任务列表 + token + 耗时）
   - 大厅看板显示 `todo/doing/done`
   - 点击“一键刷新数据”后，页面重新拉取最新 `dashboard.json`
