#!/usr/bin/env python3
import argparse
from common import load_json, write_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--alerts', required=True)
    p.add_argument('--timeline', required=True)
    p.add_argument('--brief', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()

    alerts = load_json(args.alerts)
    t = load_json(args.timeline)
    events = t.get('events', [])
    frag = t.get('fragmentation_optimization', {})

    md = "# 24h 舆情复盘报告\n\n"
    md += "## 一、原因（Cause）\n"
    md += f"- 触发机制：{', '.join(alerts['alert']['reasons']) if alerts['alert']['reasons'] else '无'}\n"
    md += f"- 主要风险主题：{events[0]['topic'] if events else '无'}\n\n"

    md += "## 二、影响（Impact）\n"
    md += f"- 总提及：{alerts['summary']['total_mentions']}\n"
    md += f"- 负向占比：{alerts['summary']['negative_ratio']}\n"
    if events:
        md += f"- Top事件峰值：{events[0]['timeline_stats']['peak_bucket']}（{events[0]['timeline_stats']['peak_count']}）\n"
    md += "\n"

    md += "## 三、处置（Action）\n"
    md += "- 已执行：告警分级、自动快报、时间线归因\n"
    md += "- 建议执行：客服统一口径、技术修复公告、重点渠道答疑\n\n"

    if frag:
        b = frag.get('before', {})
        a = frag.get('after', {})
        md += "## 四、碎片化优化前后对比\n"
        md += f"- 优化前事件数：{b.get('event_count', '-')}, 平均每事件条目：{b.get('avg_mentions_per_event', '-')}\n"
        md += f"- 优化后事件数：{a.get('event_count', '-')}, 平均每事件条目：{a.get('avg_mentions_per_event', '-')}\n"
        md += f"- 策略：{frag.get('strategy', {}).get('method', '-') }\n\n"

    md += "## 五、建议（Suggestion）\n"
    md += "1. 安全类关键词提升权重，默认拉升一级。\n"
    md += "2. 增加人工确认SLA，超时自动升级到P1。\n"
    md += "3. 补充多语言/谐音关键词词典，降低漏检。\n\n"

    md += "## 事件清单\n"
    for e in events:
        md += f"- {e['event_id']} | {e['topic']} | mentions={e['mention_count']} | channels={','.join(e['channels'])}\n"

    write_text(args.output, md)
    print(f"[retro] -> {args.output}")


if __name__ == '__main__':
    main()
