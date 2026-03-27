#!/usr/bin/env python3
import argparse
from datetime import datetime
from common import load_json, write_json


def parse(ts):
    return datetime.fromisoformat(ts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--now', default=None, help='ISO time for deterministic test')
    args = p.parse_args()

    data = load_json(args.input)
    now = parse(args.now) if args.now else datetime.now().astimezone()
    updated = 0

    for a in data.get('alerts', []):
        if a.get('status') != 'open':
            continue
        updated_at = parse(a['updated_at'])
        age_minutes = (now - updated_at).total_seconds() / 60
        if age_minutes >= a.get('escalate_after_minutes', 20):
            old = a['level']
            new = a.get('escalate_to', old)
            if new != old:
                a['level'] = new
                a['status'] = 'escalated'
                a['escalated_from'] = old
                a['escalated_at'] = now.isoformat(timespec='seconds')
                updated += 1

    data['escalation_run_at'] = now.isoformat(timespec='seconds')
    data['escalation_count'] = updated
    write_json(args.output, data)
    print(f"[escalate] escalated={updated} -> {args.output}")


if __name__ == '__main__':
    main()
