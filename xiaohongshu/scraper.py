#!/usr/bin/env python3
"""
Robust WeChat article scraper - saves incrementally
"""
import subprocess, re, json, csv, os, time
from datetime import datetime as dt

BASE = "/Users/a1/.openclaw/workspace/xiaohongshu"
os.makedirs(f"{BASE}/partial", exist_ok=True)

QUERIES = [
    ("小红书 OpenClaw 自动化", "primary"),
    ("小红书 AI 运营", "primary"),
    ("OpenClaw 内容创作", "primary"),
    ("小红书 全自动 运营", "primary"),
    ("AI 小红书 涨粉", "secondary"),
    ("小红书 爆款 技巧", "secondary"),
    ("内容运营 AI工具", "secondary"),
    ("小红书 变现 方法", "secondary"),
    ("小红书 AI自动化 发布", "primary"),
    ("OpenClaw 小红书 矩阵", "primary"),
    ("小红书 笔记 自动化", "secondary"),
    ("AI 小红书 爆款 生成", "secondary"),
    ("小红书 涨粉 自动化", "secondary"),
    ("小红书 运营 工具 AI", "secondary"),
    ("自媒体 小红书 OpenClaw", "secondary"),
    ("小红书 自动发帖 工具", "secondary"),
    ("AI 运营 小红书 技巧", "secondary"),
    ("小红书 自动 运营 工具", "secondary"),
    ("小红书 爆款 内容 创作", "secondary"),
    ("AI 小红书 笔记 自动化", "secondary"),
    ("OpenClaw 自动化 内容", "primary"),
]

def curl_html(query, page):
    import urllib.parse
    q = urllib.parse.quote(query)
    url = f"https://weixin.sogou.com/weixin?type=2&query={q}&ie=utf8&page={page}"
    cmd = [
        'curl', '-s', '--max-time', '15',
        '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        '-H', 'Accept: text/html',
        '-H', 'Accept-Language: zh-CN,zh;q=0.9',
        url
    ]
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

def parse_page(html, kw, kwtype):
    arts = []
    for item in re.findall(r'<li[^>]*id="sogou_vr_\d+_box_\d+"[^>]*>(.*?)</li>\s*<!--\s*z\s*-->', html, re.DOTALL):
        tm = re.search(r'<h3>\s*<a[^>]*>(.*?)</a>\s*</h3>', item, re.DOTALL)
        pm = re.search(r'<p class="txt-info"[^>]*>(.*?)</p>', item, re.DOTALL)
        sm = re.search(r'<div class="s-p">(.*?)</div>', item, re.DOTALL)
        title = re.sub(r'<[^>]+>', '', tm.group(1) if tm else '')
        title = re.sub(r'<!--red_beg-->|<!--red_end-->', '', title).strip()
        title = re.sub(r'\s+', ' ', title)
        summary = re.sub(r'<[^>]+>', '', pm.group(1) if pm else '')
        summary = re.sub(r'<!--red_beg-->|<!--red_end-->', '', summary).strip()
        summary = re.sub(r'\s+', ' ', summary)
        sd = re.sub(r'<[^>]+>', '', sm.group(1) if sm else '').strip()
        sd = re.sub(r'\s+', ' ', sd)
        parts = sd.split()
        source, date = parts[0] if parts else '', parts[-1] if parts else ''
        if title:
            arts.append({'title': title, 'summary': summary, 'source': source,
                         'date': date, 'keyword': kw, 'keyword_type': kwtype})
    return arts

def save_state(arts):
    # Save JSON
    with open(f"{BASE}/partial/articles_raw.json", 'w', encoding='utf-8') as f:
        json.dump(arts, f, ensure_ascii=False, indent=2)
    # Save CSV
    with open(f"{BASE}/公众号文章数据_2026-03-29.csv", 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['title','summary','source','date','keyword','keyword_type'])
        w.writeheader()
        w.writerows(arts)

def main():
    print(f"Start {dt.now()}")
    all_arts = []
    seen = set()
    
    # Load existing if any
    existing_path = f"{BASE}/partial/articles_raw.json"
    if os.path.exists(existing_path):
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                all_arts = json.load(f)
            seen = {a['title'] for a in all_arts}
            print(f"Resumed with {len(all_arts)} existing articles")
        except:
            pass
    
    for query, kwtype in QUERIES:
        print(f"\n=== {query} ===")
        for page in range(1, 11):
            html = curl_html(query, page)
            if not html or len(html) < 1000:
                print(f"  P{page}: empty/blocked, sleep 5s")
                time.sleep(5)
                continue
            if '验证' in html[:500] or '访问过于频繁' in html[:500]:
                print(f"  P{page}: blocked, sleep 8s")
                time.sleep(8)
                continue
            arts = parse_page(html, query, kwtype)
            new = [a for a in arts if a['title'] not in seen]
            for a in new:
                seen.add(a['title'])
                all_arts.append(a)
            print(f"  P{page}: +{len(new)} new ({len(all_arts)} total)")
            save_state(all_arts)
            time.sleep(1.5)
        time.sleep(2)
    
    print(f"\n\nDONE: {len(all_arts)} unique articles at {dt.now()}")
    save_state(all_arts)
    print("Saved!")

if __name__ == "__main__":
    main()
