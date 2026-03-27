# 24h 舆情复盘报告

## 一、原因（Cause）
- 触发机制：mention_count_reached, negative_ratio_exceeded
- 主要风险主题：服务可用性故障

## 二、影响（Impact）
- 总提及：16
- 负向占比：0.812
- Top事件峰值：2026-03-15 18:00（3）

## 三、处置（Action）
- 已执行：告警分级、自动快报、时间线归因
- 建议执行：客服统一口径、技术修复公告、重点渠道答疑

## 四、碎片化优化前后对比
- 优化前事件数：16, 平均每事件条目：1
- 优化后事件数：8, 平均每事件条目：2
- 策略：best-match assignment + same-topic iterative merge + time-proximity merge for tiny clusters

## 五、建议（Suggestion）
1. 安全类关键词提升权重，默认拉升一级。
2. 增加人工确认SLA，超时自动升级到P1。
3. 补充多语言/谐音关键词词典，降低漏检。

## 事件清单
- E001 | 服务可用性故障 | mentions=5 | channels=douyin,forum,weibo
- E006 | 价格争议 | mentions=3 | channels=douyin,forum,xiaohongshu
- E003 | 数据安全疑虑 | mentions=2 | channels=forum,weibo
- E004 | 数据安全疑虑 | mentions=2 | channels=douyin,xiaohongshu
- E002 | 用户维权 | mentions=1 | channels=xiaohongshu
- E005 | 其他 | mentions=1 | channels=weibo
- E007 | 服务可用性故障 | mentions=1 | channels=rss
- E008 | 数据安全疑虑 | mentions=1 | channels=rss
