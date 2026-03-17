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
grep -q "isLegacyBoardUrl" "$LOADER"
grep -q "location.replace('/board')" "$LOADER"
grep -q "location.pathname === '/board' && (location.search || location.hash)" "$LOADER"
grep -q "chatLink.setAttribute('href', '/chat?session=main')" "$LOADER"
grep -q "bindHardNavigation(chatLink, '/chat?session=main')" "$LOADER"
grep -q "location.pathname === '/chat'" "$LOADER"
echo "OK route isolation checks"

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
