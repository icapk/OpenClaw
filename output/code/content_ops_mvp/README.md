# OpenClaw 自媒体内容生产工作流 MVP

一个可直接运行的“全自动内容闭环”最小可用版本：
**选题 → 数据采集 → 文案创作 → 发布（模拟/可适配真实）→ 反馈抓取 → 周报生成**。

## 1. 目录结构

```text
output/code/content_ops_mvp/
├── config/
│   ├── config.template.json
│   └── config.json
├── data/
│   ├── topic_seeds.txt
│   ├── trending_signals.csv
│   └── feedback_metrics.csv
├── templates/
│   ├── wechat_long_article.md
│   └── xiaohongshu_image_text.md
├── scripts/
│   └── workflow.py
├── cron.example
├── daemon.sh
├── init.sh
└── run.sh
```

运行产物输出到：
- `/Users/a1/.openclaw/workspace/output/content_ops_mvp/`（全流程产物）
- `/Users/a1/.openclaw/workspace/output/reports/`（闭环报告）

## 2. 三条命令内跑通

```bash
cd /Users/a1/.openclaw/workspace/output/code/content_ops_mvp
bash init.sh
bash run.sh
```

执行后验收：
- `output/content_ops_mvp/drafts/`：自动生成草稿
- `output/content_ops_mvp/published/`：发布记录（模拟/真实适配）
- `output/content_ops_mvp/logs/workflow.log`：链路日志
- `output/reports/内容闭环报告_*.md`：完整闭环报告

## 3. 全自动说明（无手动中间环节）

`run.sh` 会自动串行执行：
1. 初始化目录与配置
2. 自动选题（topic_seeds + trending_signals + keywords）
3. 自动创作（公众号/小红书模板）
4. 自动发布（默认 simulate，可切换适配层）
5. 自动反馈落库（views/likes/favorites/conversions）
6. 自动生成周报（同时落地 runtime 和 output/reports）

## 4. 配置项（把人工步骤配置化）

编辑 `config/config.json`：
- 账号：`channels.*.account`
- 渠道开关：`channels.*.enabled`
- 模板路径：`channels.*.template`
- 发布时间：`channels.*.publish_time`
- 关键词：`workflow.keywords`
- 发布模式：`openclaw.publish_adapter`
  - `simulate`：模拟发布（默认）
  - `local_command`：执行本地 OpenClaw 命令适配真实发布
- 发布命令模板：`openclaw.local_publish_command`

## 5. OpenClaw 集成方式

### A. 本地命令发布（已内置）
在配置中设置：
```json
"openclaw": {
  "publish_adapter": "local_command",
  "local_publish_command": "openclaw message send --channel feishu --target {target} --message \"{text}\"",
  "default_target": "运营群"
}
```
并将 `workflow.dry_run_publish` 改为 `false`。

### B. 消息接口模式
可将 `local_publish_command` 替换为你自己的 webhook/脚本命令（保持 `{target}` `{text}` 占位符）。

### C. 定时机制（cron）
参考 `cron.example`，支持：
- 每日自动选题与发布
- 每周自动复盘

## 6. 守护模式（daemon）

```bash
bash daemon.sh 60
```
表示每 60 分钟自动跑一次完整链路。

## 7. 反馈闭环数据结构

`data/feedback_metrics.csv` 字段：
- `week`
- `platform`
- `title`
- `views`
- `likes`
- `favorites`
- `conversions`
- `publish_date`

## 8. 已实现自动化样例

已实现“从主题到成稿”自动化样例：
- 自动从趋势数据选取关键词
- 自动生成公众号长文与小红书图文首稿
- 自动记录发布与反馈
- 自动生成周报

## 9. 后续扩展点

1. 接入真实平台 API（公众号/小红书）替换模拟发布。
2. 增加 AB 标题测试和自动优选。
3. 接入多数据源（搜索趋势、评论关键词）提高选题质量。
4. 增加素材管理（图片、短视频脚本）和多账号矩阵分发。
