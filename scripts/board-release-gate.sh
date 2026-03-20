#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/a1/.openclaw/workspace"
GEN="$ROOT/custom-ui/board/src/generate-dashboard.js"
DATA="$ROOT/custom-ui/board/data/dashboard.json"
LOADER="$ROOT/custom-ui/board/src/loader.js"

cd "$ROOT"

echo "[gate] 1/5 generate realtime board data"
node "$GEN" >/tmp/board-gate-generate.log
cat /tmp/board-gate-generate.log

echo "[gate] 2/5 assert PM=1 & Tester=1"
node -e '
const fs=require("fs");
const d=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
const pm=d.agents.find(a=>a.id==="product")?.todoCount ?? -1;
const tester=d.agents.find(a=>a.id==="tester")?.todoCount ?? -1;
if(pm!==1){console.error(`PM todoCount expected 1, got ${pm}`); process.exit(1)}
if(tester!==1){console.error(`Tester todoCount expected 1, got ${tester}`); process.exit(1)}
console.log(`OK pm=${pm} tester=${tester}`)
' "$DATA"

echo "[gate] 3/5 assert route isolation (/board + legacy redirect + /chat)"
grep -q "const BOARD_URL = '/board'" "$LOADER"
grep -q "const LAST_BOARD_URL_KEY = 'oc-office-last-board-url'" "$LOADER"
grep -q "isLegacyBoardUrl" "$LOADER"
grep -q "const isBoardChatPath = (pathname = location.pathname) => pathname === '/board/chat' || pathname.startsWith('/board/chat/')" "$LOADER"
grep -q "const isBoardMode = (pathname = location.pathname) => isBoardPathLike(pathname) && !isBoardChatPath(pathname)" "$LOADER"
grep -q "const isBoardDashboardRoot = (pathname = location.pathname) => pathname === BOARD_URL;" "$LOADER"
grep -q "&& !u.search && !u.hash" "$LOADER"
grep -q "&& !location.search" "$LOADER"
grep -q "&& !location.hash" "$LOADER"
grep -q "history.replaceState(history.state, '', getLastBoardUrl())" "$LOADER"
grep -q "function sanitizeBoardLinks()" "$LOADER"
grep -q "chatLink.setAttribute('href', '/chat?session=main')" "$LOADER"
grep -q "bindHardNavigation(chatLink, '/chat?session=main')" "$LOADER"
grep -q "bindHardNavigation(a, normalized)" "$LOADER"
grep -q "location.assign(targetUrl)" "$LOADER"
grep -q "location.assign('/chat?session=main')" "$LOADER"
grep -q "location.pathname === '/chat'" "$LOADER"
echo "OK route isolation checks"

echo "[gate] 3.2/5 assert native /board/* pages stay reachable"
grep -q "if (!isBoardDashboardRoot(location.pathname)) return;" "$LOADER"
grep -q "const BOARD_NATIVE_SUBPATHS = new Set(\\['overview', 'sessions', 'agents', 'skills', 'nodes', 'config', 'debug', 'logs'\\]);" "$LOADER"
grep -q 'return `${BOARD_URL}/${bare}${u.search}${u.hash}`;' "$LOADER"
grep -q 'return `${BOARD_URL}/${bare}`;' "$LOADER"
grep -q "if (a.id === LINK_ID || shouldKeepBoardRootLink(a)) continue;" "$LOADER"
echo "OK board subpage reachability checks"

echo "[gate] 3.5/5 assert gateway auth failure hint (no silent fallback)"
grep -Fq "if (!res.ok)" "$LOADER"
grep -Fq "e?.status === 401 || e?.status === 403" "$LOADER"
grep -Fq "网关认证失败" "$LOADER"
echo "OK auth-failure hint checks"

echo "[gate] 4/5 assert mutual active state"
grep -q "data-oc-board-mode" "$LOADER"
grep -q "data-oc-chat-mode" "$LOADER"
grep -q "chatLink.removeAttribute('aria-current')" "$LOADER"
grep -q "boardLink.setAttribute('aria-current', 'page')" "$LOADER"
echo "OK mutual-active checks"

echo "[gate] 5/5 assert refresh stability"
first_sha=$(shasum -a 256 "$DATA" | awk '{print $1}')
first_pm=$(node -e 'const fs=require("fs"); const d=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); process.stdout.write(String(d.agents.find(a=>a.id==="product")?.todoCount ?? -1));' "$DATA")
first_tester=$(node -e 'const fs=require("fs"); const d=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); process.stdout.write(String(d.agents.find(a=>a.id==="tester")?.todoCount ?? -1));' "$DATA")
node "$GEN" >/dev/null
second_sha=$(shasum -a 256 "$DATA" | awk '{print $1}')
second_pm=$(node -e 'const fs=require("fs"); const d=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); process.stdout.write(String(d.agents.find(a=>a.id==="product")?.todoCount ?? -1));' "$DATA")
second_tester=$(node -e 'const fs=require("fs"); const d=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); process.stdout.write(String(d.agents.find(a=>a.id==="tester")?.todoCount ?? -1));' "$DATA")
node -e '
const fs=require("fs");
const d=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
if(!d.source || !String(d.source).includes("tasks/in_progress")) { console.error("source must include tasks/in_progress"); process.exit(1); }
if(!d.summary || typeof d.summary.todoItems !== "number") { console.error("summary.todoItems missing"); process.exit(1); }
console.log("OK source/summary schema");
' "$DATA"
if [[ "$first_pm" != "$second_pm" || "$first_tester" != "$second_tester" ]]; then
  echo "refresh unstable: pm($first_pm->$second_pm) tester($first_tester->$second_tester)" >&2
  exit 1
fi
echo "OK refresh stable (counts unchanged), pm=$first_pm tester=$first_tester sha1=$first_sha sha2=$second_sha"

echo "[gate] PASS all 5 assertions"
