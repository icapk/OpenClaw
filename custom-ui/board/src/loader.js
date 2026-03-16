(() => {
  const LINK_ID = 'oc-office-dashboard-link';
  const VIEW_ID = 'oc-board-native-view';
  const STYLE_ID = 'oc-board-native-style';
  const BOARD_URL = '/chat?panel=board';

  const isBoardMode = () => {
    const u = new URL(location.href);
    return u.pathname === '/chat' && u.searchParams.get('panel') === 'board';
  };

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      #${LINK_ID}[data-active="1"] { background:#f6e5e8 !important; }
      html[data-oc-board-mode="1"] a[href="/chat"] { background:transparent !important; }
      #${VIEW_ID}{padding:16px}
      #${VIEW_ID} .head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
      #${VIEW_ID} .summary{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:10px;margin-bottom:16px}
      #${VIEW_ID} .stat{border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#fff}
      #${VIEW_ID} .stat b{display:block;font-size:22px;margin-top:4px}
      #${VIEW_ID} .dept{margin-bottom:16px}
      #${VIEW_ID} .dept h3{margin:0 0 8px}
      #${VIEW_ID} .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
      #${VIEW_ID} .card{border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#fff}
      #${VIEW_ID} .badge{font-size:12px;border-radius:999px;padding:2px 8px;color:#fff;margin-left:6px}
      #${VIEW_ID} .active{background:#16a34a} #${VIEW_ID} .done{background:#64748b}
    `;
    document.head.appendChild(style);
  }

  function syncActive() {
    const boardLink = document.getElementById(LINK_ID);
    const chatLink = document.querySelector('a[href="/chat"]');
    const on = isBoardMode();
    if (boardLink) {
      boardLink.dataset.active = on ? '1' : '0';
      if (on) boardLink.setAttribute('aria-current', 'page');
      else boardLink.removeAttribute('aria-current');
    }
    if (chatLink && on) chatLink.removeAttribute('aria-current');
    document.documentElement.toggleAttribute('data-oc-board-mode', on);
  }

  function ensureLink() {
    const chatLink = document.querySelector('a[href="/chat"]');
    if (!chatLink) return;
    let boardLink = document.getElementById(LINK_ID);
    if (!boardLink) {
      boardLink = chatLink.cloneNode(true);
      boardLink.id = LINK_ID;
      boardLink.href = BOARD_URL;
      boardLink.removeAttribute('target');
      boardLink.removeAttribute('rel');
      boardLink.removeAttribute('aria-current');

      // text
      const label = Array.from(boardLink.querySelectorAll('*')).find((el) => (el.textContent || '').trim() === '聊天' || (el.textContent || '').trim().toLowerCase() === 'chat');
      if (label) label.textContent = '看板';

      // icon
      const iconWrap = boardLink.querySelector('img,svg')?.parentElement;
      if (iconWrap) {
        iconWrap.innerHTML = '<span style="font-size:14px;line-height:1">📊</span>';
      }

      boardLink.style.marginTop = '4px';
      chatLink.insertAdjacentElement('afterend', boardLink);
    }
    syncActive();
  }

  function mapDept(name = '') {
    if (name.includes('研发') || name.includes('测试') || name.includes('运维')) return '研发部';
    if (name.includes('运营')) return '运营部';
    if (name.includes('产品') || name.includes('审核') || name.includes('尚书')) return '中枢';
    return '职能部';
  }

  const fmtSec = (sec = 0) => `${Math.floor(Number(sec || 0) / 60)}m ${Math.floor(Number(sec || 0) % 60)}s`;
  const stat = (k, v) => `<div class="stat"><span>${k}</span><b>${v}</b></div>`;

  async function renderBoardIfNeeded() {
    if (!isBoardMode()) return;
    const main = document.querySelector('main');
    if (!main) return;
    ensureStyle();

    try {
      const res = await fetch(`/office/data/dashboard.json?t=${Date.now()}`);
      const data = await res.json();
      const s = data.summary || {};
      const grouped = {};
      for (const a of (data.agents || [])) {
        const d = mapDept(a.department || '');
        (grouped[d] ||= []).push(a);
      }
      const deptHtml = Object.entries(grouped).map(([d, list]) => `
        <section class="dept"><h3>${d}</h3><div class="grid">${list.map(a => `
          <article class="card">
            <div><strong>${a.name || a.id}</strong><span class="badge ${a.status === 'active' ? 'active' : 'done'}">${a.status || 'done'}</span></div>
            <div>当前任务：${a.currentTask || '（空闲）'}</div>
            <div>待办：${a.todoCount ?? 0}</div>
            <div>Token：${a.tokenUsed ?? 0}</div>
          </article>`).join('')}</div></section>`).join('');

      main.innerHTML = `<div id="${VIEW_ID}">
        <div class="head"><h2 style="margin:0">看板</h2><button id="oc-board-refresh" style="padding:8px 12px;border-radius:8px;border:1px solid #e5e7eb;cursor:pointer;">刷新</button></div>
        <section class="summary">${stat('总Agent', s.totalAgents ?? 0)}${stat('在线', s.activeAgents ?? 0)}${stat('离线', s.doneAgents ?? 0)}${stat('待办', s.todoItems ?? 0)}${stat('总耗时', fmtSec(s.totalDurationSec ?? 0))}${stat('总Token', s.totalTokens ?? 0)}</section>
        ${deptHtml}
      </div>`;
      document.getElementById('oc-board-refresh')?.addEventListener('click', renderBoardIfNeeded);
    } catch (e) {
      main.innerHTML = `<div id="${VIEW_ID}"><h2>看板</h2><p>加载失败，请重试。</p></div>`;
    }
    syncActive();
  }

  function tick() {
    ensureLink();
    renderBoardIfNeeded();
    syncActive();
  }

  tick();
  setInterval(tick, 1000);
})();
