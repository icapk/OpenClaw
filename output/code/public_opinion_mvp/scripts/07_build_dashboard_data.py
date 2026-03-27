#!/usr/bin/env python3
import argparse
from collections import Counter
from common import load_json, write_json, parse_ts


def build_trend(timeline_items):
    c = Counter()
    for x in timeline_items:
        b = parse_ts(x['time']).strftime('%Y-%m-%d %H:%M')[:-1] + '0'
        c[b] += 1
    return [{'bucket': k, 'count': v} for k, v in sorted(c.items())]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--alerts', required=True)
    p.add_argument('--timeline', required=True)
    p.add_argument('--brief', required=True)
    p.add_argument('--retro', required=True)
    p.add_argument('--weekly', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()

    alerts = load_json(args.alerts)
    timeline = load_json(args.timeline)
    frag = timeline.get('fragmentation_optimization', {})

    data = {
        'summary': alerts.get('summary', {}),
        'global_alert': alerts.get('alert', {}),
        'alerts': alerts.get('alerts', []),
        'events': timeline.get('events', []),
        'timeline': timeline.get('timeline', []),
        'timeline_graph': timeline.get('timeline_graph', {}),
        'trend_series': build_trend(timeline.get('timeline', [])),
        'fragmentation_optimization': frag,
        'reports': [
            {'name': '5W1H快报', 'path': args.brief},
            {'name': '24h复盘', 'path': args.retro},
            {'name': '周报', 'path': args.weekly},
        ]
    }
    write_json(args.output, data)
    print(f"[dashboard-data] -> {args.output}")


if __name__ == '__main__':
    main()
