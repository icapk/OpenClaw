(() => {
  const LINK_ID = 'oc-office-dashboard-link';
  const VIEW_ID = 'oc-board-native-view';
  const STYLE_ID = 'oc-board-native-style';
  const BOARD_URL = '/board';
  const BOARD_NATIVE_SUBPATHS = new Set(['overview', 'sessions', 'agents', 'skills', 'nodes', 'config', 'debug', 'logs']);
  const LAST_BOARD_URL_KEY = 'oc-office-last-board-url';
  const NAV_INTENT_KEY = 'oc-office-nav-intent';
  const BOARD_RESTORE_WINDOW_MS = 20000;
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

  const isBoardPathLike = (pathname = location.pathname) => pathname === '/board' || pathname.startsWith('/board/');
  const isBoardChatPath = (pathname = location.pathname) => pathname === '/board/chat' || pathname.startsWith('/board/chat/');
  const isBoardMode = (pathname = location.pathname) => isBoardPathLike(pathname) && !isBoardChatPath(pathname);
  const isBoardDashboardRoot = (pathname = location.pathname) => pathname === BOARD_URL;

  function rememberBoardUrl(url = `${location.pathname}${location.search}${location.hash}`) {
    try {
      const u = new URL(String(url), location.origin);
      if (u.origin !== location.origin || !isBoardMode(u.pathname)) return;
      sessionStorage.setItem(LAST_BOARD_URL_KEY, `${u.pathname}${u.search}${u.hash}`);
    } catch {}
  }

  function getLastBoardUrl() {
    if (isBoardMode(location.pathname)) {
      const current = `${location.pathname}${location.search}${location.hash}`;
      rememberBoardUrl(current);
      return current;
    }
    try {
      const saved = sessionStorage.getItem(LAST_BOARD_URL_KEY);
      if (!saved) return BOARD_URL;
      const u = new URL(saved, location.origin);
      return isBoardMode(u.pathname) ? `${u.pathname}${u.search}${u.hash}` : BOARD_URL;
    } catch {
      return BOARD_URL;
    }
  }

  function isBoardTargetUrl(url = '') {
    try {
      const u = new URL(String(url), location.origin);
      return u.origin === location.origin && isBoardMode(u.pathname);
    } catch {
      return false;
    }
  }

  function normalizeHistoryUrl(url) {
    if (!url) return url;
    try {
      const u = new URL(String(url), location.origin);
      if (u.origin !== location.origin) return url;
      if (shouldPinBoardRoute() && (u.pathname === '/chat' || u.pathname.startsWith('/chat/')) && !u.search && !u.hash) {
        return getLastBoardUrl();
      }
      if (isBoardMode(u.pathname)) {
        const next = `${u.pathname}${u.search}${u.hash}`;
        rememberBoardUrl(next);
        return next;
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

  function normalizeBoardRoute() {
    // 兼容旧链接：/chat?panel=board -> /board
    if (isLegacyBoardUrl()) {
      setNavIntent('board');
      history.replaceState(history.state, '', '/board');
      rememberBoardUrl('/board');
      return true;
    }

    // 修正错误链路：/board/chat?session=main
    // - 若最近意图是进入看板：拉回 /board（避免被主应用错误拼接到 /board/chat）
    // - 其余情况按聊天意图回主聊天链路
    if (isBoardChatPath(location.pathname)) {
      const intent = getNavIntent();
      const fresh = Date.now() - Number(intent?.ts || 0) <= BOARD_RESTORE_WINDOW_MS;
      if (intent?.mode === 'chat' && fresh) {
        history.replaceState(history.state, '', '/chat?session=main');
      } else {
        history.replaceState(history.state, '', getLastBoardUrl());
      }
      return true;
    }

    // 保留 /board/* 子路由能力，仅约束错误的 /board/chat* 回到主聊天链路。

    // 主应用若把 /board 当成未知路由回退到 /chat，按最近看板意图拉回 /board
    const intent = getNavIntent();
    const shouldRestoreBoard = location.pathname === '/chat'
      && !location.search
      && !location.hash
      && intent?.mode === 'board'
      && Date.now() - Number(intent.ts || 0) <= BOARD_RESTORE_WINDOW_MS;
    if (shouldRestoreBoard) {
      history.replaceState(history.state, '', getLastBoardUrl());
      return true;
    }

    if (isBoardMode(location.pathname)) {
      setNavIntent('board');
      rememberBoardUrl();
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
    const onBoard = isBoardMode(location.pathname);
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
    if (!link || link.__ocNavBound === true) return;
    link.__ocNavBound = true;
    link.dataset.ocNavBound = '1';
    link.addEventListener('click', (ev) => {
      if (!ev.isTrusted) return;
      const withModifier = ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button !== 0;
      if (withModifier) return;
      ev.preventDefault();
      ev.stopPropagation();
      const nextMode = isBoardTargetUrl(targetUrl) ? 'board' : 'chat';
      setNavIntent(nextMode);
      if (nextMode === 'board') rememberBoardUrl(targetUrl);
      if (location.pathname + location.search !== targetUrl) {
        location.assign(targetUrl);
      }
    }, true);
  }

  function normalizeChatHref(raw = '') {
    const href = String(raw || '').trim();
    if (!href) return null;
    if (href === 'chat' || href === './chat' || href === '../chat' || href === '/chat' || href === '/chat?session=main') return '/chat?session=main';
    if (href === '/board/chat' || href.startsWith('/board/chat?') || href.startsWith('/board/chat/')) return '/chat?session=main';
    try {
      const u = new URL(href, location.origin);
      if (u.origin !== location.origin) return null;
      if (u.pathname === '/chat' || u.pathname.endsWith('/chat')) return '/chat?session=main';
      if (u.pathname === '/board/chat' || u.pathname.startsWith('/board/chat/')) return '/chat?session=main';
    } catch {}
    return null;
  }

  function sanitizeChatLinks() {
    const links = Array.from(document.querySelectorAll('a[href]'));
    for (const a of links) {
      const normalized = normalizeChatHref(a.getAttribute('href') || a.href || '');
      if (!normalized) continue;
      a.setAttribute('href', normalized);
      bindHardNavigation(a, normalized);
    }
  }

  function normalizeBoardHref(raw = '') {
    const href = String(raw || '').trim();
    if (!href) return null;
    try {
      const u = new URL(href, location.origin);
      if (u.origin !== location.origin) return null;
      if (isBoardMode(u.pathname)) return `${u.pathname}${u.search}${u.hash}`;
      const bare = u.pathname.replace(/^\/+/, '');
      if (!isBoardMode(location.pathname) || !BOARD_NATIVE_SUBPATHS.has(bare)) return null;
      return `${BOARD_URL}/${bare}${u.search}${u.hash}`;
    } catch {
      const bare = href.replace(/^\/+/, '');
      if (!isBoardMode(location.pathname) || !BOARD_NATIVE_SUBPATHS.has(bare)) return null;
      return `${BOARD_URL}/${bare}`;
    }
  }

  function shouldKeepBoardRootLink(a) {
    if (!a) return false;
    const href = (a.getAttribute('href') || '').trim();
    if (!href) return false;
    try {
      const u = new URL(href, location.origin);
      return u.origin === location.origin && u.pathname === BOARD_URL;
    } catch {
      return href === BOARD_URL;
    }
  }

  function sanitizeBoardLinks() {
    const links = Array.from(document.querySelectorAll('a[href]'));
    for (const a of links) {
      if (a.id === LINK_ID || shouldKeepBoardRootLink(a)) continue;
      const normalized = normalizeBoardHref(a.getAttribute('href') || a.href || '');
      if (!normalized) continue;
      a.setAttribute('href', normalized);
      bindHardNavigation(a, normalized);
    }
  }

  function ensureLink() {
    sanitizeChatLinks();
    sanitizeBoardLinks();
    const chatLink = findChatLink();
    if (!chatLink) return;

    // 强制聊天入口回到主聊天链路，避免在 /board 下解析成 /board/chat
    chatLink.setAttribute('href', '/chat?session=main');
    bindHardNavigation(chatLink, '/chat?session=main');

    let boardLink = document.getElementById(LINK_ID);
    if (!boardLink) {
      boardLink = chatLink.cloneNode(true);
      boardLink.id = LINK_ID;
      // cloneNode 会复制 chatLink 的 data-oc-nav-bound=1，导致看板链接无法绑定点击接管
      boardLink.removeAttribute('data-oc-nav-bound');
      delete boardLink.dataset.ocNavBound;
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
    if (!isBoardDashboardRoot(location.pathname)) return;
    const main = document.querySelector('main');
    if (!main) return;
    ensureStyle();
    rememberBoardUrl();

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
        <div class="head"><div><h2 style="margin:0">看板</h2><div style="margin-top:4px;color:#64748b;font-size:12px">当前页面：总览</div></div><button id="oc-board-refresh" style="padding:8px 12px;border-radius:8px;border:1px solid #e5e7eb;cursor:pointer;">刷新</button></div>
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
