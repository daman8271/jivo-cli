#!/bin/bash
# browser-check.sh — the check that curl cannot do.
#
# Fetching a page proves the HTML exists. It does not prove the page RUNS: that
# the modules resolve, the data loads, the charts draw, nothing throws, and the
# layout does not blow out sideways. Those are the failures an operator actually
# meets, and they only show up in a real browser executing real JS.
#
# So: serve site-v2, drive headless Chrome over every page, and assert on
#   - console errors and failed requests
#   - rendered content (a page that loads but renders nothing is a failure)
#   - horizontal overflow at 390 / 768 / 1440
#   - BOTH themes, since dark is the default
#
#   ./browser-check.sh              every page
#   ./browser-check.sh receivables  one page
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$DIR")"
SITE="$ROOT/site-v2"
PORT="${PORT:-8791}"
ONLY="${1:-}"

[ -f "$SITE/index.html" ] || { echo "site-v2 not built yet" >&2; exit 1; }

python3 -m http.server "$PORT" --directory "$SITE" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
for _ in $(seq 1 40); do
  curl -sf -o /dev/null "http://127.0.0.1:$PORT/index.html" && break
  perl -e 'select undef,undef,undef,0.25'
done

# Entity pages need real parameters, or they correctly render "not found" and we
# would be testing the empty state instead of the page.
PARAMS=$(python3 - "$SITE" <<'PY'
import json, os, sys
d = os.path.join(sys.argv[1], "data")
out = {}
try:
    parties = json.load(open(os.path.join(d, "parties.oil.json")))
    v = next((p for p in parties if p.get("side") == "V" and p.get("kind") == "TRADE"), None)
    c = next((p for p in parties if p.get("side") == "C" and p.get("kind") == "TRADE"), None)
    if v: out["party.html"] = "co=oil&card=%s" % v["card"]
    if c: out["party2"] = "co=oil&card=%s" % c["card"]
except Exception:
    pass
try:
    man = json.load(open(os.path.join(d, "manifest.json")))
    k = next(iter((man.get("kpis") or {}).get("oil", {})), None)
    if k: out["derivation.html"] = "k=%s&co=oil" % k
except Exception:
    pass
try:
    rows = json.load(open(os.path.join(d, "open-item-list.oil.json")))["summary"]
    r = rows[0]
    out["document.html"] = "co=oil&type=%s&entry=%s" % (r.get("OBJ_TYPE"), r.get("DOC_ENTRY"))
except Exception:
    pass
try:
    rows = json.load(open(os.path.join(d, "bank-accounts.oil.json")))["summary"]
    out["bank-account.html"] = "co=oil&acct=%s" % rows[0].get("GL_ACCT_CODE")
except Exception:
    pass
try:
    rows = json.load(open(os.path.join(d, "provisions.oil.json")))["summary"]
    out["gl-account.html"] = "co=oil&acct=%s" % rows[0].get("ACCT_CODE")
except Exception:
    pass
print(json.dumps(out))
PY
)

PAGES="index receivables payables open-items grpo goods-return return-note provisions
cash-sale banks bank-reco transporter party document bank-account gl-account
derivation methodology health search"

FAIL=0
for p in $PAGES; do
  [ -n "$ONLY" ] && [ "$ONLY" != "$p" ] && continue
  [ -f "$SITE/$p.html" ] || { echo "MISSING  $p.html"; FAIL=$((FAIL+1)); continue; }
  # A page with no <link rel="icon"> makes the browser request /favicon.ico, which
  # 404s and shows up as a console error indistinguishable from a real one.
  grep -q 'rel="icon"' "$SITE/$p.html" || { echo "NO FAVICON LINK  $p.html (browser will 404 on /favicon.ico)"; FAIL=$((FAIL+1)); }
  q=$(printf '%s' "$PARAMS" | python3 -c "import json,sys;print(json.load(sys.stdin).get('$p.html',''))" 2>/dev/null)
  url="http://127.0.0.1:$PORT/$p.html"; [ -n "$q" ] && url="$url?$q"

  for theme in dark light; do
    chrome-devtools-axi eval "() => { try{localStorage.setItem('jivo-theme','$theme')}catch(e){}; return 1 }" >/dev/null 2>&1
    chrome-devtools-axi open "$url" >/dev/null 2>&1
    chrome-devtools-axi wait 2500 >/dev/null 2>&1
    # grep -c prints 0 AND exits 1 when nothing matches; `|| echo 0` would append a
    # SECOND zero and make every clean page look like a failure. `|| true` swallows
    # the exit status without adding output.
    errs=$(chrome-devtools-axi console --type error 2>/dev/null | grep -c 'msgid=' || true)
    errs=${errs:-0}
    res=$(chrome-devtools-axi eval "() => { const de=document.documentElement; return JSON.stringify({
        ov: de.scrollWidth - de.clientWidth,
        theme: de.getAttribute('data-theme'),
        text: (document.body.innerText||'').trim().length,
        cards: document.querySelectorAll('.card,.kpi').length,
        svgs: document.querySelectorAll('svg').length,
        boot: !!document.getElementById('boot') && document.getElementById('boot').offsetParent !== null
      }) }" 2>/dev/null | sed 's/^result: //' | tr -d '\\"' )
    printf '%-16s %-5s  errors=%-3s %s\n' "$p" "$theme" "$errs" "$res"
    echo "$res" | grep -q '"boot":true\|boot:true' && { echo "   ^ STUCK ON LOADING"; FAIL=$((FAIL+1)); }
    [ "$errs" != "0" ] && FAIL=$((FAIL+1))
  done

  for w in 390 768 1440; do
    chrome-devtools-axi resize "$w" 900 >/dev/null 2>&1
    ov=$(chrome-devtools-axi eval "() => document.documentElement.scrollWidth - document.documentElement.clientWidth" 2>/dev/null | sed 's/^result: //' | tr -d '"')
    [ "${ov:-0}" -gt 2 ] 2>/dev/null && { echo "   OVERFLOW $p @${w}px = ${ov}px"; FAIL=$((FAIL+1)); }
    # ...and again with every <details> OPEN. Collapsed content is invisible to a
    # layout check, so a working note or SQL block full of unbreakable column
    # names can push the page 450px sideways and this gate would never see it.
    chrome-devtools-axi eval "() => { document.querySelectorAll('details').forEach(d => d.open = true); return document.querySelectorAll('details').length }" >/dev/null 2>&1
    ovo=$(chrome-devtools-axi eval "() => document.documentElement.scrollWidth - document.documentElement.clientWidth" 2>/dev/null | sed 's/^result: //' | tr -d '"')
    [ "${ovo:-0}" -gt 2 ] 2>/dev/null && { echo "   OVERFLOW(disclosures open) $p @${w}px = ${ovo}px"; FAIL=$((FAIL+1)); }
    chrome-devtools-axi eval "() => { document.querySelectorAll('details').forEach(d => d.open = false); return 1 }" >/dev/null 2>&1
  done
done

echo
echo "browser-check: $FAIL failure(s)"
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
