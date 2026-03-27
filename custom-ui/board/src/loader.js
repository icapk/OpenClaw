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
  
  // 办公室可视化看板路径
  const isOfficeVisual = (pathname = location.pathname) => pathname === '/board/office-visual';

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
      #${VIEW_ID} .summary{display:grid;grid-template-columns:repeat(6,minmax(110px,1fr));gap:10px;margin-bottom:14px}
      #${VIEW_ID} .stat{border:1px solid #e5e7eb;border-radius:10px;padding:10px;background:#fff}
      #${VIEW_ID} .stat b{display:block;font-size:22px;margin-top:4px}
      #${VIEW_ID} .office-wrap{display:grid;grid-template-columns:2.2fr 1fr;gap:12px}
      #${VIEW_ID} .office{border:1px solid #dbe2ea;border-radius:14px;background:linear-gradient(180deg,#f7fafc,#eef4fa);padding:14px;min-height:420px;position:relative;overflow:hidden}
      #${VIEW_ID} .zones{display:grid;grid-template-columns:2fr 1fr;grid-template-rows:1fr 1fr;gap:10px;height:100%}
      #${VIEW_ID} .zone{border:1px dashed #c8d5e3;border-radius:12px;padding:10px;position:relative;background:rgba(255,255,255,.52)}
      #${VIEW_ID} .zone h3{font-size:13px;margin:0 0 8px;color:#334155}
      #${VIEW_ID} .zone.work{grid-row:1 / span 2}
      #${VIEW_ID} .avatars{display:flex;flex-wrap:wrap;gap:10px;align-content:flex-start}
      #${VIEW_ID} .avatar{width:120px;min-height:88px;border:1px solid #d7e0ea;border-radius:10px;background:#fff;padding:8px;position:relative}
      #${VIEW_ID} .avatar .name{font-size:12px;color:#111827;font-weight:600}
      #${VIEW_ID} .avatar .char{font-size:22px;line-height:1;margin-bottom:6px}
      #${VIEW_ID} .avatar .state{font-size:11px;color:#64748b}
      #${VIEW_ID} .task-bubble{position:absolute;top:-10px;left:6px;right:6px;background:#fff7d6;color:#92400e;border:1px solid #facc15;border-radius:999px;padding:2px 7px;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      #${VIEW_ID} .avatar.working{box-shadow:0 0 0 2px rgba(22,163,74,.25)}
      #${VIEW_ID} .avatar.idle{opacity:.92}
      #${VIEW_ID} .avatar.break{opacity:.92}
      #${VIEW_ID} .timeline{border:1px solid #dbe2ea;border-radius:14px;background:#fff;padding:12px}
      #${VIEW_ID} .timeline h3{margin:0 0 8px;font-size:13px}
      #${VIEW_ID} .timeline ul{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px}
      #${VIEW_ID} .timeline li{font-size:12px;color:#334155}
      #${VIEW_ID} .muted{font-size:12px;color:#64748b}
      @media (max-width: 1100px){#${VIEW_ID} .office-wrap{grid-template-columns:1fr}}
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
    
    // 添加办公室可视化看板链接
    let officeLink = document.getElementById('oc-office-visual-link');
    if (!officeLink) {
      officeLink = boardLink.cloneNode(true);
      officeLink.id = 'oc-office-visual-link';
      officeLink.removeAttribute('data-oc-nav-bound');
      delete officeLink.dataset.ocNavBound;
      officeLink.href = '/board/office-visual';
      officeLink.title = '办公室可视化看板';
      officeLink.setAttribute('aria-label', '办公室可视化看板');
      officeLink.removeAttribute('target');
      officeLink.removeAttribute('rel');
      officeLink.removeAttribute('aria-current');
      officeLink.classList.remove('active');

      const label = Array.from(officeLink.querySelectorAll('*')).find((el) => (el.textContent || '').trim() === '看板');
      if (label) label.textContent = '办公室';

      const iconWrap = officeLink.querySelector('img,svg')?.parentElement;
      if (iconWrap) iconWrap.innerHTML = '<span style="font-size:14px;line-height:1">🏢</span>';

      officeLink.style.marginTop = '4px';
      boardLink.insertAdjacentElement('afterend', officeLink);
    }
    bindHardNavigation(officeLink, '/board/office-visual');
    
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
    const res = await fetch(`/custom-ui/board/data/dashboard.json?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) {
      const err = new Error(`dashboard fetch failed: ${res.status}`);
      err.status = res.status;
      throw err;
    }
    return res.json();
  }

  async function renderBoardIfNeeded() {
    if (!isBoardDashboardRoot(location.pathname) && !isOfficeVisual(location.pathname)) return;
    const main = document.querySelector('main');
    if (!main) return;
    ensureStyle();
    rememberBoardUrl();

    try {
      const data = await loadBoardData();
      const s = data.summary || {};
      const agents = data.agents || [];
      const byName = new Map(agents.map((a) => [a.name, a]));

      const cast = [
        { name: '产品经理', icon: '🧠', role: '产品' },
        { name: '开发工程师', icon: '👨‍💻', role: '开发' },
        { name: '测试工程师', icon: '🧪', role: '测试' },
        { name: '小麦', icon: '🧑‍💼', role: '助理' },
      ].map((p, idx) => {
        const src = byName.get(p.name) || { status: 'done', currentTask: '（空闲）', todoCount: 0 };
        const working = src.status === 'active' && src.todoCount > 0;
        let mode = 'working';
        if (!working) mode = idx % 2 === 0 ? 'idle' : 'break';
        return {
          ...p,
          mode,
          task: src.currentTask || '（空闲）',
          todo: src.todoCount || 0,
        };
      });

      const modeLabel = { working: '办公中', idle: '沙发放松', break: '健身充电' };
      const inWork = cast.filter((a) => a.mode === 'working');
      const inIdle = cast.filter((a) => a.mode === 'idle');
      const inBreak = cast.filter((a) => a.mode === 'break');

      const avatarHtml = (list) => list.map((a) => `
        <article class="avatar ${a.mode}">
          ${a.mode === 'working' ? `<div class="task-bubble" title="${a.task}">${a.task}</div>` : ''}
          <div class="char">${a.icon}</div>
          <div class="name">${a.name}</div>
          <div class="state">${modeLabel[a.mode]}｜待办 ${a.todo}</div>
        </article>`).join('') || '<div class="muted">暂无人员</div>';

      const timeline = cast.map((a) => `<li><strong>${a.name}</strong>：${modeLabel[a.mode]}${a.mode === 'working' ? `（${a.task}）` : ''}</li>`).join('');

      main.innerHTML = `<div id="${VIEW_ID}">
        <div class="head"><div><h2 style="margin:0">办公室看板（Beta）</h2><div style="margin-top:4px;color:#64748b;font-size:12px">PJT-18789-BOARD｜当前页面：总览</div></div><button id="oc-board-refresh" style="padding:8px 12px;border-radius:8px;border:1px solid #e5e7eb;cursor:pointer;">刷新</button></div>
        <section class="summary">${stat('总Agent', s.totalAgents ?? 0)}${stat('在线', s.activeAgents ?? 0)}${stat('离线', s.doneAgents ?? 0)}${stat('待办', s.todoItems ?? 0)}${stat('总耗时', fmtSec(s.totalDurationSec ?? 0))}${stat('总Token', s.totalTokens ?? 0)}</section>
        <div class="office-wrap">
          <section class="office">
            <div class="zones">
              <div class="zone work"><h3>工位区（Working）</h3><div class="avatars">${avatarHtml(inWork)}</div></div>
              <div class="zone lounge"><h3>沙发区（Idle）</h3><div class="avatars">${avatarHtml(inIdle)}</div></div>
              <div class="zone gym"><h3>健身区（Break）</h3><div class="avatars">${avatarHtml(inBreak)}</div></div>
            </div>
          </section>
          <aside class="timeline">
            <h3>动态速览</h3>
            <ul>${timeline}</ul>
            <p class="muted" style="margin-top:10px">说明：工作中会显示头顶任务气泡；空闲人员会进入沙发/健身区。</p>
          </aside>
        </div>
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
