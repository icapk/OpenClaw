#!/usr/bin/env python3
import argparse
import subprocess
from common import load_json, write_text, now_iso


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--channels', required=True)
    p.add_argument('--brief', required=True)
    p.add_argument('--retro', required=True)
    p.add_argument('--weekly', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()

    cfg = load_json(args.channels)
    feishu = cfg.get('feishu_doc', {})
    enabled = bool(feishu.get('enabled', False))
    mode = feishu.get('mode', 'mock')  # mock / openclaw
    doc_token = feishu.get('doc_token', 'mock_doc_token')

    content = []
    content.append(f"[{now_iso()}] feishu_doc_enabled={enabled}")
    content.append(f"mode={mode}")
    content.append(f"target_doc_token={doc_token}")
    content.append(f"brief_path={args.brief}")
    content.append(f"retro_path={args.retro}")
    content.append(f"weekly_path={args.weekly}")

    if not enabled or mode != 'openclaw':
        content.append('status=mock_only (未启用真实调用，保持mock链路)')
    else:
        # 真实调用适配：默认尝试 openclaw CLI；失败则优雅降级为mock
        cmd = feishu.get('real_command')
        if not cmd:
            cmd = [
                'openclaw', 'feishu-doc', 'append',
                '--doc-token', doc_token,
                '--content', f"自动同步报告\n- brief: {args.brief}\n- retro: {args.retro}\n- weekly: {args.weekly}"
            ]
        try:
            proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
            content.append('status=real_sent')
            out = (proc.stdout or '').strip().replace('\n', ' | ')
            if out:
                content.append(f'cli_output={out}')
        except FileNotFoundError:
            content.append('status=mock_fallback')
            content.append('reason=openclaw_cli_not_found')
        except subprocess.CalledProcessError as e:
            content.append('status=mock_fallback')
            err = ((e.stderr or '') + ' ' + (e.stdout or '')).strip().replace('\n', ' | ')
            content.append(f'reason=permission_or_runtime_error detail={err}')
        except Exception as e:
            content.append('status=mock_fallback')
            content.append(f'reason=unexpected_error detail={e}')

    write_text(args.output, '\n'.join(content) + '\n')
    print(f"[feishu-adapter] mode={mode} enabled={enabled} -> {args.output}")


if __name__ == '__main__':
    main()
