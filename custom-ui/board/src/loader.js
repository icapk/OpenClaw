(() => {
  const LINK_ID = 'oc-office-dashboard-link';
  const VIEW_ID = 'oc-board-native-view';
  const STYLE_ID = 'oc-board-native-style';
  const BOARD_URL = '/board';
  const NAV_INTENT_KEY = 'oc-office-nav-intent';
  const BOARD_RESTORE_WINDOW_MS = 4000;
  const rawReplaceState = history.replaceState.bind(history);
  const rawPushState = history.pushState.bind(history);

  function setNavIntent(mode) {
    try {
      sessionStorage.setItem(NAV_INTENT_KEY, JSON.stringify({ mode, ts: Date.now() }));
    } catch {}
  }

  function getNavIntent() {
    try {
      return JSON.parse(sessionStorage.getItem(NAV_INTENT_KEY) || 'null');
    } catch {
      return null;
    }
  }

  function shouldPinBoardRoute() {
    const intent = getNavIntent();
    return intent?.mode === 'board' && Date.now() - Number(intent.ts || 0) <= BOARD_RESTORE_WINDOW_MS;
  }

  function normalizeHistoryUrl(url) {
    if (!url) return url;
    try {
      const u = new URL(String(url), location.origin);
      if (u.origin !== location.origin) return url;
      if (shouldPinBoardRoute() && (u.pathname === '/chat' || u.pathname.startsWith('/chat/'))) {
        return '/board';
      }
      if (u.pathname === '/board' || u.pathname.startsWith('/board/')) {
        return '/board';
      }
      return `${u.pathname}${u.search}${u.hash}`;
    } catch {
      return url;
    }
  }

  history.replaceState = function replaceStatePatched(state, title, url) {
    return rawReplaceState(state, title, normalizeHistoryUrl(url));
  };

  history.pushState = function pushStatePatched(state, title, url) {
    return rawPushState(state, title, normalizeHistoryUrl(url));
  };

  const isLegacyBoardUrl = () => {
    const u = new URL(location.href);
    return u.pathname === '/chat' && u.searchParams.get('panel') === 'board';
  };

  const isBoardPathLike = (pathname = location.pathname) => pathname === '/board' || pathname.startsWith('/board/');
  const isBoardMode = () => isBoardPathLike(location.pathname);

  function normalizeBoardRoute() {
    // 兼容旧链接：/chat?panel=board -> /board
    if (isLegacyBoardUrl()) {
      setNavIntent('board');
      location.replace('/board');
      return true;
    }

    // 修正错误链路：/board/chat?session=main -> /chat?session=main
    if (location.pathname === '/board/chat' || location.pathname.startsWith('/board/chat/')) {
      setNavIntent('chat');
      location.replace('/chat?session=main');
      return true;
    }

    // /board 仅看板，禁止其它 /board/* 视图（除了上面的 /board/chat 已被转正）
    if (location.pathname !== '/board' && isBoardPathLike(location.pathname)) {
      setNavIntent('board');
      history.replaceState(history.state, '', '/board');
      return true;
    }

    // /board 必须保持纯净，避免刷新后带着旧 query/hash 回退到错误链路
    if (location.pathname === '/board' && (location.search || location.hash)) {
      setNavIntent('board');
      history.replaceState(history.state, '', '/board');
      return true;
    }

    // 主应用若把 /board 当成未知路由回退到 /chat，按最近看板意图拉回 /board
    const intent = getNavIntent();
    const shouldRestoreBoard = location.pathname === '/chat'
      && intent?.mode === 'board'
      && Date.now() - Number(intent.ts || 0) <= BOARD_RESTORE_WINDOW_MS;
    if (shouldRestoreBoard) {
      history.replaceState(history.state, '', '/board');
      return true;
    }

    if (location.pathname === '/board') {
      setNavIntent('board');
    }

    return false;
  }

  if (normalizeBoardRoute()) {
    // 路由被规范化后继续执行，确保UI状态同步
  }

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      #${LINK_ID}[data-active="1"] { background:#f6e5e8 !important; }
      html[data-oc-board-mode="1"] a[href^="/chat"] { background:transparent !important; }
      html[data-oc-chat-mode="1"] #${LINK_ID} { background:transparent !important; }
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

  function findChatLink() {
    return Array.from(document.querySelectorAll('a[href]')).find((a) => {
      const raw = (a.getAttribute('href') || '').trim();
      if (!raw) return false;
      if (raw === '/chat' || raw === '/chat?session=main' || raw === 'chat' || raw === './chat' || raw === '../chat') return true;
      try {
        const u = new URL(a.href, location.origin);
        return u.pathname === '/chat' || u.pathname.endsWith('/chat');
      } catch {
        return false;
      }
    }) || null;
  }

  function syncActive() {
    const boardLink = document.getElementById(LINK_ID);
    const chatLink = findChatLink();
    const onBoard = isBoardMode();
    const onChat = location.pathname === '/chat';

    if (boardLink) {
      boardLink.dataset.active = onBoard ? '1' : '0';
      boardLink.classList.toggle('active', onBoard);
      if (onBoard) boardLink.setAttribute('aria-current', 'page');
      else boardLink.removeAttribute('aria-current');
    }

    if (chatLink) {
      chatLink.classList.toggle('active', onChat);
      if (onBoard) chatLink.removeAttribute('aria-current');
      if (onChat) chatLink.setAttribute('aria-current', 'page');
      if (!onChat) chatLink.removeAttribute('aria-current');
    }

    document.documentElement.toggleAttribute('data-oc-board-mode', onBoard);
    document.documentElement.toggleAttribute('data-oc-chat-mode', onChat);
  }

  function bindHardNavigation(link, targetUrl) {
    if (!link || link.dataset.ocNavBound === '1') return;
    link.dataset.ocNavBound = '1';
    link.addEventListener('click', (ev) => {
      if (!ev.isTrusted) return;
      const withModifier = ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button !== 0;
      if (withModifier) return;
      ev.preventDefault();
      ev.stopPropagation();
      setNavIntent(targetUrl === BOARD_URL ? 'board' : 'chat');
      if (location.pathname + location.search !== targetUrl) location.assign(targetUrl);
    }, true);
  }

  function ensureLink() {
    const chatLink = findChatLink();
    if (!chatLink) return;

    // 强制聊天入口回到主聊天链路，避免在 /board 下解析成 /board/chat
    chatLink.setAttribute('href', '/chat?session=main');
    bindHardNavigation(chatLink, '/chat?session=main');

    let boardLink = document.getElementById(LINK_ID);
    if (!boardLink) {
      boardLink = chatLink.cloneNode(true);
      boardLink.id = LINK_ID;
      boardLink.href = BOARD_URL;
      boardLink.title = '看板';
      boardLink.setAttribute('aria-label', '看板');
      boardLink.removeAttribute('target');
      boardLink.removeAttribute('rel');
      boardLink.removeAttribute('aria-current');
      boardLink.classList.remove('active');

      const label = Array.from(boardLink.querySelectorAll('*')).find((el) => (el.textContent || '').trim() === '聊天' || (el.textContent || '').trim().toLowerCase() === 'chat');
      if (label) label.textContent = '看板';

      const iconWrap = boardLink.querySelector('img,svg')?.parentElement;
      if (iconWrap) iconWrap.innerHTML = '<span style="font-size:14px;line-height:1">📊</span>';

      boardLink.style.marginTop = '4px';
      chatLink.insertAdjacentElement('afterend', boardLink);
    }
    bindHardNavigation(boardLink, '/board');
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

  async function loadBoardData() {
    const res = await fetch(`/office/data/dashboard.json?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) {
      const err = new Error(`dashboard fetch failed: ${res.status}`);
      err.status = res.status;
      throw err;
    }
    return res.json();
  }

  async function renderBoardIfNeeded() {
    if (!isBoardMode()) return;
    const main = document.querySelector('main');
    if (!main) return;
    ensureStyle();

    try {
      const data = await loadBoardData();
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
      const isAuthErr = e?.status === 401 || e?.status === 403;
      const msg = isAuthErr
        ? `网关认证失败（${e.status}）。请先完成网关登录/鉴权后重试；当前仍停留在 /board，不会跳转到聊天。`
        : '看板加载失败，请稍后重试。';
      main.innerHTML = `<div id="${VIEW_ID}"><h2>看板</h2><p style="color:${isAuthErr ? '#b91c1c' : '#334155'}">${msg}</p><button id="oc-board-refresh" style="padding:8px 12px;border-radius:8px;border:1px solid #e5e7eb;cursor:pointer;">重试</button></div>`;
      document.getElementById('oc-board-refresh')?.addEventListener('click', renderBoardIfNeeded);
    }
    syncActive();
  }

  function guardChatNavigation() {
    if (document.documentElement.dataset.ocChatGuardBound === '1') return;
    document.documentElement.dataset.ocChatGuardBound = '1';
    document.addEventListener('click', (ev) => {
      if (!ev.isTrusted) return;
      const a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
      if (!a) return;
      const href = (a.getAttribute('href') || '').trim();
      const isChatIntent = href === 'chat' || href === './chat' || href === '../chat' || href === '/chat' || href === '/chat?session=main' || href.includes('/chat');
      if (!isChatIntent) return;
      const withModifier = ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button !== 0;
      if (withModifier) return;
      ev.preventDefault();
      ev.stopPropagation();
      setNavIntent('chat');
      location.assign('/chat?session=main');
    }, true);
  }

  function tick() {
    normalizeBoardRoute();
    ensureLink();
    renderBoardIfNeeded();
    syncActive();
  }

  guardChatNavigation();
  tick();
  setInterval(tick, 1000);
})();
