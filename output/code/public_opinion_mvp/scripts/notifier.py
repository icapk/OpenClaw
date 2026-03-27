#!/usr/bin/env python3
import argparse
import subprocess
from common import load_json, write_text, now_iso


def build_message(alerts):
    return (
        f"[舆情告警] level={alerts['alert']['level']} triggered={alerts['alert']['triggered']} "
        f"reasons={','.join(alerts['alert']['reasons'])} total={alerts['summary']['total_mentions']}"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--channels', required=True, help='config/channels.json')
    p.add_argument('--alerts', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()

    ch_cfg = load_json(args.channels)
    alerts = load_json(args.alerts)
    msg_cfg = ch_cfg.get('message', {})

    mode = msg_cfg.get('mode', 'simulate')
    enabled = msg_cfg.get('enabled', False)
    target = msg_cfg.get('target', '#ops-war-room')
    channel = msg_cfg.get('channel', '')

    msg = build_message(alerts)
    line = f"[{now_iso()}] mode={mode} target={target} {msg}"

    send_result = 'mock'
    if mode == 'openclaw' and enabled:
        cmd = ['openclaw', 'message', 'send', '--target', target, '--message', msg]
        if channel:
            cmd.extend(['--channel', channel])
        try:
            proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
            send_result = 'sent'
            stdout = (proc.stdout or '').strip().replace('\n', ' | ')
            if stdout:
                line += f' cli_output="{stdout}"'
        except FileNotFoundError:
            send_result = 'degraded_to_mock'
            line += ' sent=false reason=openclaw_cli_not_found'
        except subprocess.CalledProcessError as e:
            send_result = 'degraded_to_mock'
            err = ((e.stderr or '') + ' ' + (e.stdout or '')).strip().replace('\n', ' | ')
            line += f' sent=false reason=permission_or_runtime_error detail="{err}"'
        except Exception as e:
            send_result = 'degraded_to_mock'
            line += f' sent=false reason=unexpected_error detail="{e}"'
    else:
        line += ' sent=mock'

    line += f' result={send_result}'
    write_text(args.output, line + '\n')
    print(f"[notify] mode={mode} result={send_result} -> {args.output}")


if __name__ == '__main__':
    main()
