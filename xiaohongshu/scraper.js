// Browser-based scraper for WeChat articles
// This script collects article data by navigating Sogou Weixin search pages

const BASE_URL = "https://weixin.sogou.com/weixin";
const KEYWORDS = [
  "小红书 OpenClaw 自动化",
  "小红书 AI 运营",
  "OpenClaw 内容创作",
  "小红书 全自动 运营",
  "AI 小红书 涨粉",
  "小红书 爆款 技巧",
  "内容运营 AI工具",
  "小红书 变现 方法",
  "小红书 AI自动化 发布",
  "OpenClaw 小红书 矩阵",
  "小红书 笔记 自动化",
  "AI 小红书 爆款 生成",
  "小红书 涨粉 自动化",
  "小红书 运营 工具 AI",
  "自媒体 小红书 OpenClaw",
  "小红书 自动发帖 工具",
];

let allArticles = [];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function extractArticlesFromPage() {
  const items = document.querySelectorAll('li.pos-item');
  const articles = [];
  
  items.forEach(item => {
    const titleEl = item.querySelector('h3');
    const descEl = item.querySelector('.txt-info') || item.querySelector('p');
    const infoEl = item.querySelector('.s-p') || item.querySelector('.account');
    
    let title = '';
    let summary = '';
    let source = '';
    let date = '';
    
    if (titleEl) {
      title = titleEl.innerText || titleEl.textContent;
    }
    
    if (descEl) {
      summary = descEl.innerText || descEl.textContent;
    }
    
    if (infoEl) {
      const infoText = infoEl.innerText || infoEl.textContent;
      const parts = infoText.split(/\s+/);
      source = parts[0] || '';
      date = parts[parts.length - 1] || '';
    }
    
    if (title) {
      articles.push({ title: title.trim(), summary: summary.trim(), source, date });
    }
  });
  
  return articles;
}

async function scrapeKeyword(keyword, maxPages = 10) {
  const encodedKeyword = encodeURIComponent(keyword);
  const articles = [];
  
  for (let page = 1; page <= maxPages; page++) {
    const url = `${BASE_URL}?type=2&query=${encodedKeyword}&ie=utf8&page=${page}`;
    console.log(`[${keyword}] Loading page ${page}...`);
    
    window.location.href = url;
    await sleep(3000); // Wait for page load
    
    const pageArticles = extractArticlesFromPage();
    console.log(`[${keyword}] Page ${page}: found ${pageArticles.length} articles`);
    
    articles.push(...pageArticles.map(a => ({ ...a, keyword })));
    await sleep(1500); // Be polite
  }
  
  return articles;
}

async function main() {
  for (const keyword of KEYWORDS) {
    console.log(`\n=== Starting keyword: ${keyword} ===`);
    try {
      const articles = await scrapeKeyword(keyword, 10);
      allArticles.push(...articles);
      console.log(`Keyword '${keyword}' total: ${articles.length} articles`);
    } catch (e) {
      console.error(`Error with keyword '${keyword}':`, e);
    }
    await sleep(2000);
  }
  
  console.log('\n\n=== FINAL RESULT ===');
  console.log(JSON.stringify(allArticles, null, 2));
}

main();
