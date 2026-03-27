#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    args = p.parse_args()

    root = Path(args.root)
    s = root / 'scripts'
    py = 'python3'

    paths = {
        'sources': root / 'config/sources.json',
        'monitor': root / 'config/monitor.json',
        'channels': root / 'config/channels.json',
        'raw': root / 'output/raw_items.json',
        'alerts': root / 'output/alerts/events_alerts.json',
        'timeline': root / 'output/timeline/events_timeline.json',
        'brief': root / 'output/briefs/event_brief_5w1h.md',
        'retro': root / 'output/reports/retro_24h.md',
        'weekly': root / 'output/reports/weekly_summary.md',
        'notice': root / 'output/notifications/message_simulated.log',
        'feishu': root / 'output/notifications/feishu_doc_adapter.log',
        'dash': root / 'output/dashboard/dashboard_data.json',
        'health': root / 'output/health/selfcheck.json',
        'checklist': root / 'output/reports/最终功能清单_v1.0.md'
    }

    run([py, str(s / '01_collect.py'), '--config', str(paths['sources']), '--output', str(paths['raw'])])
    run([py, str(s / '02_detect_alerts.py'), '--monitor', str(paths['monitor']), '--input', str(paths['raw']), '--output', str(paths['alerts'])])
    run([py, str(s / '02b_escalate_alerts.py'), '--input', str(paths['alerts']), '--output', str(paths['alerts'])])
    run([py, str(s / '03_cluster_timeline.py'), '--input', str(paths['alerts']), '--output', str(paths['timeline'])])
    run([py, str(s / '04_generate_brief.py'), '--alerts', str(paths['alerts']), '--timeline', str(paths['timeline']), '--output', str(paths['brief'])])
    run([py, str(s / '05_generate_retro.py'), '--alerts', str(paths['alerts']), '--timeline', str(paths['timeline']), '--brief', str(paths['brief']), '--output', str(paths['retro'])])
    run([py, str(s / '06_generate_weekly.py'), '--alerts', str(paths['alerts']), '--timeline', str(paths['timeline']), '--output', str(paths['weekly'])])
    run([py, str(s / 'notifier.py'), '--channels', str(paths['channels']), '--alerts', str(paths['alerts']), '--output', str(paths['notice'])])
    run([py, str(s / 'feishu_doc_adapter.py'), '--channels', str(paths['channels']), '--brief', str(paths['brief']), '--retro', str(paths['retro']), '--weekly', str(paths['weekly']), '--output', str(paths['feishu'])])
    run([py, str(s / '07_build_dashboard_data.py'), '--alerts', str(paths['alerts']), '--timeline', str(paths['timeline']), '--brief', str(paths['brief']), '--retro', str(paths['retro']), '--weekly', str(paths['weekly']), '--output', str(paths['dash'])])
    run([py, str(s / 'selfcheck.py'), '--root', str(root), '--output', str(paths['health'])])
    run([py, str(s / '08_generate_completion_checklist.py'), '--output', str(paths['checklist'])])

    print('\n[workflow] DONE')
    for k, v in paths.items():
        print(f"- {k}: {v}")


if __name__ == '__main__':
    main()
