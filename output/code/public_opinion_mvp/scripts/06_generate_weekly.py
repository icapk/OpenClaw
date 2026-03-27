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

    md = "# 舆情周报汇总（自动）\n\n"
    md += "## 本周总览\n"
    md += f"- 事件数：{len(events)}\n"
    md += f"- 总提及：{alerts['summary']['total_mentions']}\n"
    md += f"- 告警等级：{alerts['alert']['level']}\n\n"
    md += "## 多事件汇总\n"
    for e in events:
        md += f"- {e['event_id']} {e['topic']} | 提及={e['mention_count']} | 峰值={e['timeline_stats']['peak_bucket']}\n"

    md += "\n## 下周关注\n- 安全类事件复发率\n- 服务故障峰值时段\n- 涨价争议舆情扩散路径\n"
    write_text(args.output, md)
    print(f"[weekly] -> {args.output}")


if __name__ == '__main__':
    main()
