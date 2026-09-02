#!/bin/bash
# live-refresh.sh — keeps the JIVO Transporter Board current, on the VPS.
#
# Same three safeguards as the Accounts Board loop it is modelled on:
#   1. flock     — a slow build never stacks on the previous one.
#   2. change detection — fingerprint of the four data sections (per-file
#      sha256 from manifest.json; as_of-only, no timestamp) against what was
#      last published. Nothing changed -> no deploy.
#   3. cadence gate — off-hours, only on the half hour.
#
# Install (VPS):   */2 * * * * /root/jivo-cli/transporter-dashboard/pipeline/live-refresh.sh
# Log: pipeline/live-refresh.log   State: pipeline/.last-published.sha256
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
SITE="$DIR/../site"
LOG="$DIR/live-refresh.log"
LOCK="$DIR/.live-refresh.lock"
STATE="$DIR/.last-published.sha256"
FAILS="$DIR/.consecutive-failures"
LASTOK="$DIR/.last-success"
PROJECT="jivo-transporter"
URL="https://${PROJECT}.vercel.app"
NOTIFY="$DIR/../../accounts-dashboard/pipeline/notify-fleet.sh"

export PATH="/usr/local/bin:/usr/bin:/bin:/root/.local/bin:/opt/homebrew/bin:$HOME/.hermes/node/bin"
export HANA_ENV_FILE="${HANA_ENV_FILE:-$DIR/../../connections/hana-vps.env}"
export HANA_BRIDGE_CMD="${HANA_BRIDGE_CMD:-true}"
[ "$(uname -s)" = "Linux" ] && export HANA_SQL_BIN="${HANA_SQL_BIN:-/usr/local/bin/hana-sql}"

ACTIVE_FROM=${ACTIVE_FROM:-7}
ACTIVE_TO=${ACTIVE_TO:-23}

log() { printf '%s %s\n' "$(date '+%F %T %Z')" "$*" >> "$LOG"; }

exec 9>"$LOCK"
flock -n 9 || exit 0

H=$(TZ=Asia/Kolkata date +%-H); M=$(TZ=Asia/Kolkata date +%-M)
if [ "$H" -lt "$ACTIVE_FROM" ] || [ "$H" -ge "$ACTIVE_TO" ]; then
  [ $((M % 30)) -eq 0 ] || exit 0
  log "$(printf 'off-hours tick (%02d:%02d IST)' "$H" "$M")"
fi

bump_fail() {
  local n; n=$(( $(cat "$FAILS" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$FAILS"
  if [ "$n" -eq 3 ] || [ $(( n % 30 )) -eq 0 ]; then
    log "ALERT after $n consecutive failures: $1"
    [ -x "$NOTIFY" ] && "$NOTIFY" "JIVO Transporter Board: $n consecutive build failures — $1" 2>/dev/null || true
  fi
}
clear_fail() { : > "$FAILS"; date -u +%FT%TZ > "$LASTOK"; }

preflight() {
  local bin="${HANA_SQL_BIN:-$DIR/../../hana-sql/hana-sql}"
  [ -x "$bin" ] || { echo "hana-sql not executable at $bin"; return 1; }
  "$bin" --help >/dev/null 2>&1; local rc=$?
  if [ "$rc" -eq 126 ] || [ "$rc" -eq 127 ]; then
    echo "hana-sql at $bin cannot execute on $(uname -s)/$(uname -m) (rc=$rc)"; return 1
  fi
  local missing=""
  for q in transporter-master transporter-invoices transporter-payments transporter-allocations; do
    [ -f "$DIR/sql/$q.sql" ] || missing="$missing $q"
  done
  [ -z "$missing" ] || { echo "missing SQL:$missing"; return 1; }
  [ -f "$SITE/index.html" ] || { echo "site/index.html missing — nothing to publish"; return 1; }
  return 0
}
if ! PFOUT=$(preflight 2>&1); then log "PREFLIGHT FAIL — $PFOUT"; bump_fail "$PFOUT"; exit 1; fi

START=$(date +%s)
if ! OUT=$(cd "$DIR" && python3 build.py 2>&1); then
  log "BUILD FAILED — previous deployment still serving"
  printf '%s\n' "$OUT" | tail -5 >> "$LOG"
  bump_fail "build.py failed: $(printf '%s\n' "$OUT" | tail -1)"
  exit 1
fi

# Fingerprint = sha256 over the ROWS of every section file, fixed order.
# generated_at (in every file) and build_seconds are deliberately excluded —
# they move every run and would force a deploy every tick.
HASH=$(python3 - "$SITE/data" <<'PY'
import json,sys,hashlib,os
d=sys.argv[1]; m=json.load(open(os.path.join(d,"manifest.json")))
if not m.get("ok", True) or m.get("errors"): sys.exit(3)
h=hashlib.sha256()
for s in sorted(m["sections"]):
    for co in sorted(m["sections"][s]):
        e=m["sections"][s][co]
        if e.get("error"): sys.exit(3)
        f=json.load(open(os.path.join(d,e["file"])))
        # rows only: generated_at lives in every file and moves every run
        h.update(f"{s}.{co}:".encode()); h.update(json.dumps(f.get("rows"),sort_keys=True,separators=(",",":")).encode())
print(h.hexdigest())
PY
) || { log "BUILD REPORTED ERRORS — not publishing"; bump_fail "manifest has errors"; exit 1; }

PREV=$(cat "$STATE" 2>/dev/null || echo "")
ELAPSED=$(( $(date +%s) - START ))
if [ "$HASH" = "$PREV" ]; then clear_fail; log "no change (${ELAPSED}s build)"; exit 0; fi

if ! (cd "$SITE" && vercel deploy --prod --yes >/dev/null 2>&1); then
  log "DEPLOY FAILED — previous deployment still serving"; bump_fail "vercel deploy failed"; exit 1
fi
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$URL" || echo "000")
if [ "$CODE" != "200" ]; then
  python3 "$DIR/vercel-public.py" "$PROJECT" >/dev/null 2>&1 || true
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$URL" || echo "000")
fi
echo "$HASH" > "$STATE"; clear_fail
log "PUBLISHED (${ELAPSED}s build, HTTP $CODE)"
[ "$CODE" = "200" ] || log "WARNING: $URL not answering 200 logged-out"
