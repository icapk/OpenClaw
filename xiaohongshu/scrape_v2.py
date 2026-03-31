#!/usr/bin/env python3
"""
WeChat Article Scraper v2 - Uses curl for reliable fetching
"""
import subprocess
import re
import json
import csv
import os
import time
from datetime import datetime

OUTPUT_DIR = "/Users/a1/.openclaw/workspace/xiaohongshu"

SEARCH_QUERIES = [
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
    # Additional keywords to boost count
    ("AI 运营 小红书 技巧", "secondary"),
    ("小红书 自动 运营 工具", "secondary"),
    ("小红书 爆款 内容 创作", "secondary"),
    ("AI 小红书 笔记 自动化", "secondary"),
    ("OpenClaw 自动化 内容", "primary"),
]

CURL_COOKIES = ""  # Will try without first

def fetch_page(query, page):
    """Fetch a Sogou Weixin search page using curl"""
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://weixin.sogou.com/weixin?type=2&query={encoded_query}&ie=utf8&page={page}"
    
    cmd = [
        'curl', '-s', '-A',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
        '-H', f'Referer: https://weixin.sogou.com/weixin?type=2&query={encoded_query}&ie=utf8',
        '--cookie', CURL_COOKIES,
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=20)
        return result.stdout.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  Error: {e}")
        return ""

def parse_articles(html, keyword, keyword_type):
    """Parse articles from HTML"""
    articles = []
    
    # Split by each article <li>
    # Pattern: each article is in a <li> with class containing article info
    li_pattern = r'<li[^>]*id="sogou_vr_\d+_box_\d+"[^>]*>(.*?)</li>\s*\n?\s*<!--\s*z\s*-->'
    
    items = re.findall(li_pattern, html, re.DOTALL)
    
    for item in items:
        try:
            # Title: inside <h3><a>...</a></h3>
            title_match = re.search(r'<h3>\s*<a[^>]*>(.*?)</a>\s*</h3>', item, re.DOTALL)
            title = title_match.group(1) if title_match else ""
            
            # Remove <em> tags (highlighting)
            title = re.sub(r'<em><!--red_beg-->(.*?)<!--red_end--></em>', r'\1', title)
            title = re.sub(r'<[^>]+>', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Summary: in <p class="txt-info">
            summary_match = re.search(r'<p class="txt-info"[^>]*>(.*?)</p>', item, re.DOTALL)
            summary = summary_match.group(1) if summary_match else ""
            summary = re.sub(r'<em><!--red_beg-->(.*?)<!--red_end--></em>', r'\1', summary)
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = re.sub(r'\s+', ' ', summary).strip()
            
            # Source and date: in <div class="s-p">
            sp_match = re.search(r'<div class="s-p">(.*?)</div>', item, re.DOTALL)
            source_date = sp_match.group(1) if sp_match else ""
            source_date = re.sub(r'<[^>]+>', '', source_date)
            source_date = re.sub(r'\s+', ' ', source_date).strip()
            
            # Parse source and date
            parts = source_date.split()
            source = parts[0] if parts else ""
            date = parts[-1] if parts else ""
            
            if title:
                articles.append({
                    'title': title,
                    'summary': summary,
                    'source': source,
                    'date': date,
                    'keyword': keyword,
                    'keyword_type': keyword_type,
                })
        except Exception as e:
            continue
    
    return articles

def main():
    print(f"Starting scrape at {datetime.now()}")
    all_articles = []
    seen_titles = set()
    
    for query, keyword_type in SEARCH_QUERIES:
        print(f"\n=== '{query}' ({keyword_type}) ===")
        for page in range(1, 11):
            html = fetch_page(query, page)
            
            if not html or "验证" in html[:500]:
                print(f"  Page {page}: Blocked or empty, skipping")
                time.sleep(3)
                continue
            
            articles = parse_articles(html, query, keyword_type)
            
            # Deduplicate
            new_count = 0
            for a in articles:
                if a['title'] not in seen_titles:
                    seen_titles.add(a['title'])
                    all_articles.append(a)
                    new_count += 1
            
            print(f"  Page {page}: {len(articles)} found, {new_count} new (total: {len(all_articles)})")
            
            if len(articles) == 0:
                time.sleep(3)
            else:
                time.sleep(1.5)
        
        time.sleep(2)
    
    print(f"\n\n=== TOTAL: {len(all_articles)} unique articles ===")
    
    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, "公众号文章数据_2026-03-29.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'summary', 'source', 'date', 'keyword', 'keyword_type'])
        writer.writeheader()
        writer.writerows(all_articles)
    print(f"Saved CSV: {csv_path}")
    
    # Save JSON backup
    json_path = os.path.join(OUTPUT_DIR, "partial/articles_raw.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON: {json_path}")

if __name__ == "__main__":
    main()
