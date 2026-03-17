const fs = require('fs');
const path = require('path');

const BASE = 'http://127.0.0.1:18789';
const DEBUG = 'http://127.0.0.1:9222';
const outDir = '/Users/a1/.openclaw/workspace/output/reports/screenshots';
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 12);

const clickTargets = [
  { name: 'overview', href: '/board/overview' },
  { name: 'sessions', href: '/board/sessions' },
  { name: 'agents', href: '/board/agents' },
  { name: 'config', href: '/board/config' },
  { name: 'logs', href: '/board/logs' },
];

const screenshotPages = [
  '/board',
  '/board/overview',
  '/board/agents',
  '/board/config',
  '/board/logs',
  '/chat?session=main',
];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getJson(url, init) {
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${url}`);
  }
  return res.json();
}

class Cdp {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.seq = 0;
    this.pending = new Map();
    this.events = [];
  }

  async connect() {
    await new Promise((resolve, reject) => {
      this.ws.addEventListener('open', resolve, { once: true });
      this.ws.addEventListener('error', reject, { once: true });
      this.ws.addEventListener('message', (event) => {
        const msg = JSON.parse(String(event.data));
        if (msg.id) {
          const pending = this.pending.get(msg.id);
          if (!pending) return;
          this.pending.delete(msg.id);
          if (msg.error) pending.reject(new Error(JSON.stringify(msg.error)));
          else pending.resolve(msg.result);
          return;
        }
        this.events.push(msg);
      });
    });
  }

  send(method, params = {}) {
    const id = ++this.seq;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  async waitFor(method, timeoutMs = 10000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const index = this.events.findIndex((event) => event.method === method);
      if (index >= 0) {
        const [event] = this.events.splice(index, 1);
        return event.params || {};
      }
      await sleep(100);
    }
    throw new Error(`timeout waiting for ${method}`);
  }

  async close() {
    this.ws.close();
    await new Promise((resolve) => {
      this.ws.addEventListener('close', resolve, { once: true });
      setTimeout(resolve, 500);
    });
  }
}

async function evalJson(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  return result.result ? result.result.value : undefined;
}

async function getState(cdp) {
  return evalJson(cdp, `
    JSON.stringify({
      href: location.href,
      pathname: location.pathname,
      search: location.search,
      title: document.title,
      boardTitle: document.querySelector('#oc-board-native-view h2')?.textContent || '',
      routeLabel: document.querySelector('#oc-board-native-view .head div div')?.textContent || '',
      hasBoardView: !!document.getElementById('oc-board-native-view'),
      chatHref: document.querySelector('a[href="/chat?session=main"]')?.getAttribute('href') || '',
      boardHref: document.querySelector('#oc-office-dashboard-link')?.getAttribute('href') || ''
    })
  `).then((v) => JSON.parse(v));
}

async function waitForState(cdp, expectedPath, expectBoardView) {
  for (let i = 0; i < 40; i += 1) {
    const state = await getState(cdp);
    const ready = state.pathname === expectedPath && (!expectBoardView || state.hasBoardView);
    if (ready) return state;
    await sleep(250);
  }
  return getState(cdp);
}

async function navigate(cdp, url) {
  cdp.events.length = 0;
  await cdp.send('Page.navigate', { url });
  await cdp.waitFor('Page.loadEventFired', 15000).catch(() => null);
  await sleep(1500);
}

async function clickHref(cdp, href) {
  const rect = await evalJson(cdp, `
    (() => {
      const href = ${JSON.stringify(href)};
      const link = Array.from(document.querySelectorAll('a[href]'))
        .find((a) => a.getAttribute('href') === href);
      if (!link) return null;
      const r = link.getBoundingClientRect();
      return {
        x: r.left + (r.width / 2),
        y: r.top + (r.height / 2),
      };
    })()
  `);
  if (!rect) {
    throw new Error(`link not found: ${href}`);
  }
  await cdp.send('Input.dispatchMouseEvent', {
    type: 'mouseMoved',
    x: rect.x,
    y: rect.y,
    button: 'left',
  });
  await cdp.send('Input.dispatchMouseEvent', {
    type: 'mousePressed',
    x: rect.x,
    y: rect.y,
    button: 'left',
    clickCount: 1,
  });
  await cdp.send('Input.dispatchMouseEvent', {
    type: 'mouseReleased',
    x: rect.x,
    y: rect.y,
    button: 'left',
    clickCount: 1,
  });
  await sleep(1500);
}

async function saveScreenshot(cdp, page) {
  const safe = page
    .replace(/^\//, '')
    .replace(/[/?=&]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '') || 'board';
  const file = path.join(outDir, `${safe}-${stamp}.png`);
  fs.mkdirSync(outDir, { recursive: true });
  const shot = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true });
  fs.writeFileSync(file, Buffer.from(shot.data, 'base64'));
  return file;
}

async function main() {
  const target = await getJson(`${DEBUG}/json/new?about:blank`, { method: 'PUT' });
  const cdp = new Cdp(target.webSocketDebuggerUrl);
  await cdp.connect();

  try {
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: 1440,
      height: 1100,
      deviceScaleFactor: 1,
      mobile: false,
    });

    const results = [];

    await navigate(cdp, `${BASE}/board`);
    results.push({ step: 'open-board', ...await waitForState(cdp, '/board', true) });

    for (const targetLink of clickTargets) {
      await navigate(cdp, `${BASE}/board`);
      await waitForState(cdp, '/board', true);
      await clickHref(cdp, targetLink.href);
      results.push({ step: `click-${targetLink.name}`, ...await waitForState(cdp, targetLink.href, true) });
    }

    await navigate(cdp, `${BASE}/board`);
    await waitForState(cdp, '/board', true);
    await clickHref(cdp, '/chat?session=main');
    results.push({ step: 'click-chat', ...await waitForState(cdp, '/chat', false) });

    const screenshots = [];
    for (const page of screenshotPages) {
      await navigate(cdp, `${BASE}${page}`);
      const expectedPath = page.startsWith('/chat') ? '/chat' : page;
      const state = await waitForState(cdp, expectedPath, !page.startsWith('/chat'));
      screenshots.push({ page, file: await saveScreenshot(cdp, page), state });
    }

    console.log(JSON.stringify({ stamp, results, screenshots }, null, 2));
  } finally {
    await cdp.close();
    await fetch(`${DEBUG}/json/close/${target.id}`).catch(() => {});
  }
}

main().catch((error) => {
  console.error(error.stack || String(error));
  process.exit(1);
});
