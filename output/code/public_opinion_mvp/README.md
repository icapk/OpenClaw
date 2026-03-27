# 舆情作战中台 v1.0（完整版，可验收）

> 目标：本地一键跑通“采集→清洗去重→告警分级与升级→事件聚类与时间线→快报/复盘/周报→通知适配→Dashboard展示→自动验收报告”。

## 1. 核心增强（本次补救项）

1) **聚类优化（减少碎片化）**
- 聚类策略升级为：`best-match assignment + same-topic iterative merge`
- 可调参数：`--assign-threshold` / `--merge-threshold` / `--baseline-threshold`
- 输出优化前后对比指标到：
  - `output/timeline/events_timeline.json` 的 `fragmentation_optimization`
  - `output/reports/retro_24h.md`
  - Dashboard 碎片化对比卡片

2) **数据采集鲁棒性**
- RSS/HTTP 增加重试、超时、重试间隔配置（`config/sources.json` -> `fetch`）
- 失败自动 fallback 到 sample，并记录原因：
  - `output/raw_items.json.meta.fetch_logs`
  - `output/raw_items.json.meta.fallback_records`

3) **真实通知链路联调**
- `notifier.py` 支持 `message.mode=openclaw` + `enabled=true` 实发模式
- 无权限/命令失败自动降级 mock，不影响主流程
- 联调结果见：`output/notifications/message_simulated.log`

4) **feishu_doc 适配增强**
- `feishu_doc.mode=mock/openclaw` 可切换
- 真实调用失败优雅降级为 mock 并记录原因
- 联调日志：`output/notifications/feishu_doc_adapter.log`

5) **Dashboard 增强**
- 新增 10 分钟桶趋势可视化（折线+柱）
- 新增事件碎片化优化前后对比卡片

6) **完整验收脚本**
- `run_full_demo.sh`：执行完整链路 + 自动调用验收脚本
- `run_acceptance.sh`：自动产出 `output/reports/验收报告.md`（逐项通过/失败）

7) **文档与清单**
- 本 README 升级为完整版
- 自动生成：`output/reports/最终功能清单_v1.0.md`

---

## 2. 目录结构

```text
public_opinion_mvp/
├── run_full_demo.sh
├── run_acceptance.sh
├── config/
│   ├── sources.json
│   ├── monitor.json
│   └── channels.json
├── scripts/
│   ├── 01_collect.py
│   ├── 02_detect_alerts.py
│   ├── 02b_escalate_alerts.py
│   ├── 03_cluster_timeline.py
│   ├── 04_generate_brief.py
│   ├── 05_generate_retro.py
│   ├── 06_generate_weekly.py
│   ├── 07_build_dashboard_data.py
│   ├── 08_generate_completion_checklist.py
│   ├── notifier.py
│   ├── feishu_doc_adapter.py
│   ├── selfcheck.py
│   └── workflow.py
├── web/
│   └── index.html
└── output/
```

## 3. 快速开始

### 环境要求
- Python 3.9+
- 无第三方依赖（仅标准库）

### 一键完整演示（含验收）

```bash
cd /Users/a1/.openclaw/workspace/output/code/public_opinion_mvp
./run_full_demo.sh
```

### 单独执行验收

```bash
./run_acceptance.sh
```

Dashboard：`http://127.0.0.1:8099`（可通过 `PORT=8100 ./run_full_demo.sh` 修改端口）

## 4. 配置说明

### `config/sources.json`
- `sources`：sample/rss/http_json 数据源
- `fetch.retries`：重试次数
- `fetch.timeout_sec`：超时秒数
- `fetch.retry_interval_sec`：重试间隔
- `fetch.fallback_to_sample`：失败时是否回退 sample

### `config/channels.json`
- `message.mode`: `simulate` / `openclaw`
- `message.enabled`: 是否启用 message 发送
- `feishu_doc.mode`: `mock` / `openclaw`
- `feishu_doc.enabled`: 是否启用 feishu_doc 实调

## 5. 关键输出路径

- 采集结果（含 fetch/fallback 元信息）：`output/raw_items.json`
- 告警结果：`output/alerts/events_alerts.json`
- 聚类与时间线（含碎片化优化对比）：`output/timeline/events_timeline.json`
- 快报：`output/briefs/event_brief_5w1h.md`
- 24h复盘（含优化前后指标）：`output/reports/retro_24h.md`
- 周报：`output/reports/weekly_summary.md`
- 通知链路日志：`output/notifications/message_simulated.log`
- Feishu适配日志：`output/notifications/feishu_doc_adapter.log`
- Dashboard数据：`output/dashboard/dashboard_data.json`
- 验收报告：`output/reports/验收报告.md`
- 最终功能清单：`output/reports/最终功能清单_v1.0.md`

## 6. 常见问题

1) **openclaw 实发失败？**
- 查看 `output/notifications/message_simulated.log` 与 `output/notifications/feishu_doc_adapter.log` 中 `reason` 字段。
- 即使失败，流程会自动降级 mock，不会中断。

2) **没有趋势图或对比卡片？**
- 先确认已执行 `./run_full_demo.sh` 并刷新 Dashboard。

3) **如何验证补救项是否全部通过？**
- 打开 `output/reports/验收报告.md` 查看逐项状态。
