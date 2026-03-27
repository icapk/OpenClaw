#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import write_json


REQUIRED = [
    'output/alerts/events_alerts.json',
    'output/timeline/events_timeline.json',
    'output/briefs/event_brief_5w1h.md',
    'output/reports/retro_24h.md',
    'output/reports/weekly_summary.md',
    'output/dashboard/dashboard_data.json',
    'web/index.html'
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()

    root = Path(args.root)
    checks = []
    ok = True
    for rel in REQUIRED:
        fp = root / rel
        exists = fp.exists()
        size = fp.stat().st_size if exists else 0
        checks.append({'path': rel, 'exists': exists, 'size': size})
        if not exists:
            ok = False

    write_json(args.output, {'ok': ok, 'checks': checks})
    print(f"[selfcheck] ok={ok} -> {args.output}")


if __name__ == '__main__':
    main()
