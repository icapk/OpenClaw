#!/usr/bin/env python3
"""
WeChat Article Scraper for 小红书+OpenClaw+AI运营 topics
Collects article metadata from Sogou Weixin search
"""
import urllib.request
import urllib.parse
import json
import re
import time
import csv
import os
from datetime import datetime

OUTPUT_DIR = "/Users/a1/.openclaw/workspace/xiaohongshu"

# Keywords to search
SEARCH_QUERIES = [
    # Primary keywords
    ("小红书 OpenClaw 自动化", "primary"),
    ("小红书 AI 运营", "primary"),
    ("OpenClaw 内容创作", "primary"),
    ("小红书 全自动 运营", "primary"),
    # Secondary keywords
    ("AI 小红书 涨粉", "secondary"),
    ("小红书 爆款 技巧", "secondary"),
    ("内容运营 AI工具", "secondary"),
    ("小红书 变现 方法", "secondary"),
    # Additional variations
    ("小红书 AI自动化 发布", "primary"),
    ("OpenClaw 小红书 矩阵", "primary"),
    ("小红书 笔记 自动化", "secondary"),
    ("AI 小红书 爆款 生成", "secondary"),
    ("小红书 涨粉 自动化", "secondary"),
    ("小红书 运营 工具 AI", "secondary"),
    ("自媒体 小红书 OpenClaw", "secondary"),
    ("小红书 自动发帖 工具", "secondary"),
]

def search_sogou(query, page=1):
    """Search Sogou Weixin and return article data"""
    encoded_query = urllib.parse.quote(query)
    url = f"https://weixin.sogou.com/weixin?type=2&s_from=input&query={encoded_query}&ie=utf8&page={page}&sug=none&num=10"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://weixin.sogou.com/',
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
        return html
    except Exception as e:
        print(f"  Error fetching page {page} for '{query}': {e}")
        return None

def parse_articles(html, query, keyword_type):
    """Parse article data from Sogou search results page"""
    articles = []
    if not html:
        return articles
    
    # Pattern to match article entries
    # Each article is in a listitem with specific structure
    pattern = r'<li[^>]*class="[^"]*pos\-item[^"]*"[^>]*>(.*?)</li>'
    # Try alternative patterns
    
    # Pattern 2: match the article box more broadly
    items = re.findall(r'<li[^>]*>(?:(?!</li>).)*?<h3[^>]*>(.*?)</h3>(?:(?!</li>).)*?<p[^>]*class="s-p"?[^>]*>(.*?)</p>(?:(?!</li>).)*?<div[^>]*>(?:(?!</li>).)*?</li>', html, re.DOTALL)
    
    # Alternative: parse each result block
    # The structure is: title in h3, summary in p, source/date in a div
    
    # Find all article blocks using a simpler approach
    html_blocks = re.split(r'<li[^>]*class="[^"]*pos\-item[^"]*"', html)
    
    for i, block in enumerate(html_blocks[1:], 1):  # Skip first empty split
        try:
            # Extract title
            title_match = re.search(r'<h3[^>]*>(.*?)</h3>', block, re.DOTALL)
            title = title_match.group(1) if title_match else ""
            # Clean HTML from title
            title = re.sub(r'<[^>]+>', '', title).strip()
            title = re.sub(r'\s+', ' ', title)
            
            # Extract summary/description
            summary_match = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
            summary = summary_match.group(1) if summary_match else ""
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            summary = re.sub(r'\s+', ' ', summary)
            
            # Extract source and date
            source_date_match = re.search(r'<div[^>]*>(.*?)</div>', block, re.DOTALL)
            source_date = source_date_match.group(1) if source_date_match else ""
            source_date = re.sub(r'<[^>]+>', '', source_date).strip()
            source_date = re.sub(r'\s+', ' ', source_date)
            
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
                    'keyword': query,
                    'keyword_type': keyword_type,
                    'search_page': i,
                })
        except Exception as e:
            continue
    
    return articles

def scrape_all():
    """Main scraping function"""
    all_articles = []
    seen_titles = set()
    
    for query, keyword_type in SEARCH_QUERIES:
        print(f"\nSearching: '{query}' ({keyword_type})")
        for page in range(1, 11):  # 10 pages per keyword
            print(f"  Page {page}...", end=" ", flush=True)
            html = search_sogou(query, page)
            if html:
                articles = parse_articles(html, query, keyword_type)
                # Deduplicate
                new_articles = []
                for a in articles:
                    if a['title'] not in seen_titles:
                        seen_titles.add(a['title'])
                        new_articles.append(a)
                all_articles.extend(new_articles)
                print(f"found {len(new_articles)} new articles (total: {len(all_articles)})")
            time.sleep(1)  # Be polite
        time.sleep(2)  # Extra delay between queries
    
    return all_articles

def save_csv(articles, filepath):
    """Save articles to CSV"""
    if not articles:
        print("No articles to save!")
        return
    
    fieldnames = ['title', 'summary', 'source', 'date', 'keyword', 'keyword_type', 'search_page']
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(articles)
    
    print(f"\nSaved {len(articles)} articles to {filepath}")

if __name__ == "__main__":
    print(f"Starting WeChat article scrape at {datetime.now()}")
    print(f"Keywords: {len(SEARCH_QUERIES)}")
    
    articles = scrape_all()
    
    print(f"\n\nTotal unique articles collected: {len(articles)}")
    
    # Save raw data
    csv_path = os.path.join(OUTPUT_DIR, "公众号文章数据_2026-03-29.csv")
    save_csv(articles, csv_path)
    
    # Also save a backup
    backup_path = os.path.join(OUTPUT_DIR, "partial/raw_articles_backup.json")
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"Backup saved to {backup_path}")
    print("Done!")
