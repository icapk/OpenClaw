#!/usr/bin/env python3
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: str, text: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    items = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def parse_ts(ts: str):
    return datetime.fromisoformat(ts)


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def normalize_text(text: str) -> str:
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'[@#][\w\u4e00-\u9fa5_-]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text


def is_noise(text: str, min_len: int, blocked_patterns: List[str]) -> bool:
    if not text or len(text.strip()) < min_len:
        return True
    for p in blocked_patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            return True
    return False


def stable_id(*parts: str) -> str:
    raw = '||'.join(parts)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]


def token_set(text: str):
    t = normalize_text(text)
    toks = re.findall(r'[a-z0-9\u4e00-\u9fa5]+', t)
    return set(tok for tok in toks if len(tok) >= 2)


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))
