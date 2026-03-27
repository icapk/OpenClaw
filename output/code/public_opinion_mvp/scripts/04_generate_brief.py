#!/usr/bin/env python3
import argparse
from common import load_json, write_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--alerts', required=True)
    p.add_argument('--timeline', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()

    alerts = load_json(args.alerts)
    events = load_json(args.timeline).get('events', [])
    if not events:
        write_text(args.output, '# 5W1H 快报\n\n无有效事件。')
        return

    top = events[0]
    md = f"""# 舆情事件快报（5W1H）

## 5W1H
- **What**：{top['topic']}（提及 {top['mention_count']}）
- **When**：{top['start_time']} ~ {top['end_time']}
- **Where**：{'、'.join(top['channels'])}
- **Who**：品牌A用户、潜在受影响用户、客服与运营团队
- **Why**：关键词命中 + 负向情绪抬升 + 讨论量波峰
- **How**：建议 30 分钟内发布事实澄清，并同步技术排查进展

## 告警摘要
- 全局告警：{alerts['alert']['level']}（triggered={alerts['alert']['triggered']}）
- 风险分：{alerts['summary'].get('risk_score', 0)}
- 触发条件：{', '.join(alerts['alert']['reasons']) if alerts['alert']['reasons'] else '无'}

## 三维归因（Top 事件）
- 渠道：{top['attribution']['channel']}
- 主题：{top['attribution']['topic']}
- 情绪：{top['attribution']['sentiment']}

## 代表样本
"""
    for i, t in enumerate(top['sample_texts'], start=1):
        md += f"{i}. {t}\n"

    write_text(args.output, md)
    print(f"[brief] -> {args.output}")


if __name__ == '__main__':
    main()
