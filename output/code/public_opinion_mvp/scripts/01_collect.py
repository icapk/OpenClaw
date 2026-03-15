#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

from common import read_jsonl, write_json, normalize_text, is_noise, stable_id


def collect_sample(source):
    return read_jsonl(source['path'])


def fetch_with_retry(url, timeout_sec=10, retries=2, retry_interval_sec=1, headers=None):
    headers = headers or {'User-Agent': 'Mozilla/5.0'}
    req = Request(url, headers=headers)
    last_err = None
    for i in range(retries + 1):
        try:
            with urlopen(req, timeout=timeout_sec) as resp:
                return resp.read(), i
        except (URLError, HTTPError, TimeoutError, OSError, ValueError) as e:
            last_err = e
            if i < retries:
                time.sleep(retry_interval_sec)
    raise RuntimeError(f"fetch_failed url={url} retries={retries+1} error={last_err}")


def collect_rss(source, retry_cfg):
    raw, attempts = fetch_with_retry(
        source['url'],
        timeout_sec=retry_cfg['timeout_sec'],
        retries=retry_cfg['retries'],
        retry_interval_sec=retry_cfg['retry_interval_sec'],
    )
    root = ET.fromstring(raw)
    items = []

    for idx, it in enumerate(root.findall('.//item')):
        title = (it.findtext('title') or '').strip()
        desc = (it.findtext('description') or '').strip()
        pub = (it.findtext('pubDate') or '').strip()
        text = f"{title} {desc}".strip()
        ts = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
        if pub:
            try:
                from email.utils import parsedate_to_datetime
                ts = parsedate_to_datetime(pub).astimezone().isoformat(timespec='seconds')
            except Exception:
                pass
        items.append({
            'id': f"rss_{idx+1}",
            'timestamp': ts,
            'channel': source.get('channel', 'rss'),
            'author': source.get('author', 'rss_bot'),
            'text': text,
            'source_type': 'rss',
            'fetch_attempts': attempts + 1,
        })
    return items


def collect_http_json(source, retry_cfg):
    raw, attempts = fetch_with_retry(
        source['url'],
        timeout_sec=retry_cfg['timeout_sec'],
        retries=retry_cfg['retries'],
        retry_interval_sec=retry_cfg['retry_interval_sec'],
    )
    data = json.loads(raw.decode('utf-8'))
    rows = data if isinstance(data, list) else data.get('items', [])
    out = []
    for i, r in enumerate(rows):
        out.append({
            'id': str(r.get('id', f'http_{i+1}')),
            'timestamp': r.get('timestamp', datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')),
            'channel': r.get('channel', source.get('channel', 'http')),
            'author': r.get('author', 'http_api'),
            'text': r.get('text', ''),
            'source_type': 'http',
            'fetch_attempts': attempts + 1,
        })
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True, help='config/sources.json')
    p.add_argument('--output', required=True)
    args = p.parse_args()

    if not os.path.exists(args.config):
        print(f"[collect][error] 配置文件不存在: {args.config}", file=sys.stderr)
        print("[collect][hint] 请检查 --config 路径是否正确，例如: config/sources.json", file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[collect][error] 配置文件JSON格式错误: {args.config} ({e})", file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        print(f"[collect][error] 读取配置文件失败: {args.config} ({e})", file=sys.stderr)
        sys.exit(2)

    clean_cfg = cfg.get('cleaning', {})
    min_len = clean_cfg.get('min_text_len', 6)
    blocked = clean_cfg.get('blocked_patterns', [])

    retry_cfg = cfg.get('fetch', {})
    retry_cfg = {
        'retries': int(retry_cfg.get('retries', 2)),
        'timeout_sec': int(retry_cfg.get('timeout_sec', 10)),
        'retry_interval_sec': float(retry_cfg.get('retry_interval_sec', 1)),
        'fallback_to_sample': bool(retry_cfg.get('fallback_to_sample', True)),
    }

    collected = []
    fetch_logs = []
    fetch_errors = []
    fallback_records = []

    enabled_sources = [s for s in cfg.get('sources', []) if s.get('enabled', True)]
    sample_sources = [s for s in enabled_sources if s.get('type') == 'sample']

    for src in enabled_sources:
        st = src.get('type')
        src_name = src.get('name', st)
        try:
            if st == 'sample':
                rows = collect_sample(src)
            elif st == 'rss':
                rows = collect_rss(src, retry_cfg)
            elif st == 'http_json':
                rows = collect_http_json(src, retry_cfg)
            else:
                rows = []
            collected.extend(rows)
            fetch_logs.append({'source': src_name, 'type': st, 'status': 'ok', 'count': len(rows)})
        except Exception as e:
            err = {'source': src_name, 'type': st, 'error': str(e)}
            fetch_errors.append(err)
            fetch_logs.append({'source': src_name, 'type': st, 'status': 'failed', 'error': str(e)})

            if st in ('rss', 'http_json') and retry_cfg['fallback_to_sample'] and sample_sources:
                fallback_src = sample_sources[0]
                try:
                    fallback_rows = collect_sample(fallback_src)
                    tagged = []
                    for row in fallback_rows:
                        x = dict(row)
                        x['source_type'] = f"fallback_{st}_sample"
                        x['fallback_reason'] = str(e)
                        tagged.append(x)
                    collected.extend(tagged)
                    fallback_records.append({
                        'failed_source': src_name,
                        'fallback_source': fallback_src.get('name', 'sample'),
                        'fallback_count': len(tagged),
                        'reason': str(e)
                    })
                    fetch_logs.append({
                        'source': src_name,
                        'type': st,
                        'status': 'fallback_sample',
                        'fallback_source': fallback_src.get('name', 'sample'),
                        'count': len(tagged)
                    })
                except Exception as fe:
                    fetch_logs.append({
                        'source': src_name,
                        'type': st,
                        'status': 'fallback_failed',
                        'error': str(fe)
                    })

    deduped = []
    seen = set()
    dropped_noise = 0
    dropped_dup = 0

    for x in collected:
        raw_text = x.get('text', '').strip()
        if is_noise(raw_text, min_len=min_len, blocked_patterns=blocked):
            dropped_noise += 1
            continue
        norm = normalize_text(raw_text)
        sid = stable_id(x.get('channel', ''), norm)
        if sid in seen:
            dropped_dup += 1
            continue
        seen.add(sid)
        x['normalized_text'] = norm
        x['dedup_key'] = sid
        deduped.append(x)

    deduped.sort(key=lambda r: r.get('timestamp', ''))
    result = {
        'meta': {
            'total_collected': len(collected),
            'total_after_cleaning': len(deduped),
            'dropped_noise': dropped_noise,
            'dropped_duplicate': dropped_dup,
            'fetch_errors': fetch_errors,
            'fetch_logs': fetch_logs,
            'fallback_records': fallback_records,
            'fetch_policy': retry_cfg,
        },
        'items': deduped
    }
    write_json(args.output, result)
    print(
        f"[collect] collected={len(collected)} cleaned={len(deduped)} "
        f"dup={dropped_dup} noise={dropped_noise} fallback={len(fallback_records)} -> {args.output}"
    )


if __name__ == '__main__':
    main()
