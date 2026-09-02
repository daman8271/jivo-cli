#!/bin/bash
# live-refresh.sh — keeps the JIVO Accounts Board current, on the VPS.
#
# Runs from cron every 2 minutes. Three things make that safe to do against a
# production ERP:
#
#   1. A LOCK. flock means a slow build can never stack on top of the previous
#      one. If a run is still going, this tick exits immediately and quietly.
#
#   2. CHANGE DETECTION. It hashes the freshly-built data (ignoring the build
#      timestamp, which changes every run by definition) against what was last
#      published. Nothing changed -> no publish. Overnight and over a quiet lunch
#      that means zero publishes, so the data moves only when a human actually
#      posted something in SAP.
#
#   3. A CADENCE GATE. Outside the working day the full build is skipped
#      entirely except on the half hour. The books do not move at 04:00 and
#      querying production 720 times a night to prove it is waste.
#
# The page polls data.json on its own, so an open tab picks up a new build
# without anyone reloading.
#
# Install (on the VPS):
#   */2 * * * * /root/jivo-cli/accounts-dashboard/pipeline/live-refresh.sh
#
# Log: pipeline/live-refresh.log   State: pipeline/.last-published.sha256
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
SITE="$DIR/../site"
LOG="$DIR/live-refresh.log"
LOCK="$DIR/.live-refresh.lock"
STATE="$DIR/.last-published.sha256"
FAILS="$DIR/.consecutive-failures"
LASTOK="$DIR/.last-success"
# Data is NOT deployed to Vercel (as of 2026-08-24). The free plan allows 100
# deploys per rolling 24h across the whole account; a busy SAP day needs 60+
# publishes × 2 boards and the quota died by mid-morning, leaving v2 8.5 hours
# stale. Now each verified build lands in $PUBROOT, accounts-data-serve.py
# (systemd: accounts-data.service, 127.0.0.1:7799) hands it to Traefik, and
# both Vercel sites carry a rewrite (/data.json, /data/*) that proxies here.
# Vercel deploys happen only when the HTML itself changes — by hand.
PUBROOT="${PUBROOT:-/srv/accounts-data}"
PROJECT="jivo-accounts"
V2PROJECT="jivo-accounts-v2"
V2URL="https://${V2PROJECT}.vercel.app"
URL="https://${PROJECT}.vercel.app"

export PATH="/usr/local/bin:/usr/bin:/bin:/root/.local/bin"
export HANA_ENV_FILE="${HANA_ENV_FILE:-/root/jivo-cli/connections/hana-vps.env}"
export HANA_BRIDGE_CMD="${HANA_BRIDGE_CMD:-true}"   # VPS is already at the endpoint
# The repo ships a darwin/arm64 hana-sql; on Linux use the natively-built one,
# else every tick dies with "Exec format error" and the board silently freezes.
[ "$(uname -s)" = "Linux" ] && export HANA_SQL_BIN="${HANA_SQL_BIN:-/usr/local/bin/hana-sql}"
# Same story for the MSSQL client the budget-heads builder uses (JSAP is a
# second system on a second box). Optional: if it is missing or JSAP is down,
# that section keeps its last good figures and the SAP board still publishes.
[ "$(uname -s)" = "Linux" ] && export DSR_BIN="${DSR_BIN:-/root/jivo-cli/dsr-cli/dsr-linux}"
export SAVE_RAW=0        # no per-query debug TSVs on a 720-runs-a-day loop

# Working day in IST. Outside it, only run on the half hour.
ACTIVE_FROM=${ACTIVE_FROM:-7}
ACTIVE_TO=${ACTIVE_TO:-23}

log() { printf '%s %s\n' "$(date '+%F %T %Z')" "$*" >> "$LOG"; }

# ── lock ────────────────────────────────────────────────────────────────────
exec 9>"$LOCK"
if ! flock -n 9; then
  # Previous run still going. Silent by design — at a 2-minute cadence an
  # "already running" line every tick would bury the real events.
  exit 0
fi

# ── cadence gate ────────────────────────────────────────────────────────────
H=$(TZ=Asia/Kolkata date +%-H)
M=$(TZ=Asia/Kolkata date +%-M)
if [ "$H" -lt "$ACTIVE_FROM" ] || [ "$H" -ge "$ACTIVE_TO" ]; then
  if [ $((M % 30)) -ne 0 ]; then exit 0; fi
  log "$(printf 'off-hours tick (%02d:%02d IST)' "$H" "$M")"
fi

# ── failure bookkeeping ─────────────────────────────────────────────────────
# A build that fails is not the problem. A build that fails QUIETLY, for hours,
# while the last good deployment keeps serving numbers that look live — that is
# the problem, and it happened on 2026-08-22: a darwin/arm64 hana-sql was pulled
# onto this Linux box and every tick died with "Exec format error" for five
# hours. Nobody was told. So: count failures, and escalate on a streak.
bump_fail() {
  local n reason="$1"
  n=$(( $(cat "$FAILS" 2>/dev/null || echo 0) + 1 ))
  echo "$n" > "$FAILS"
  if [ "$n" -eq 3 ] || [ $(( n % 30 )) -eq 0 ]; then
    log "ALERT after $n consecutive failures: $reason"
    "$DIR/notify-fleet.sh" "JIVO Accounts Board: $n consecutive build failures — $reason" 2>/dev/null || true
  fi
}
clear_fail() { : > "$FAILS"; date -u +%FT%TZ > "$LASTOK"; }

# ── preflight ───────────────────────────────────────────────────────────────
# Cheap, and it turns a silent five-hour freeze into a named failure on tick 1.
# Each check is something that has actually broken this pipeline.
preflight() {
  local bin="${HANA_SQL_BIN:-$DIR/../../hana-sql/hana-sql}"
  [ -x "$bin" ]                 || { echo "hana-sql not executable at $bin"; return 1; }
  # Exec it and look ONLY at whether the kernel could run it. A healthy hana-sql
  # exits 2 on --help and 1 on no args, so "non-zero" is not a fault; 126 is
  # "cannot execute" (this is what a Mach-O on Linux gives) and 127 is not-found.
  "$bin" --help >/dev/null 2>&1; local rc=$?
  if [ "$rc" -eq 126 ] || [ "$rc" -eq 127 ]; then
    echo "hana-sql at $bin cannot execute on this OS ($(uname -s)/$(uname -m), rc=$rc) — wrong-architecture binary?"; return 1
  fi
  local missing=""
  for q in vendor-ageing customer-ageing open-item-list grpo goods-return \
           return-note provisions cash-sale bank-accounts bank-reco transporter; do
    [ -f "$DIR/sql/$q.sql" ] || missing="$missing $q"
  done
  [ -z "$missing" ] || { echo "missing SQL:$missing"; return 1; }
  return 0
}

if ! PFOUT=$(preflight 2>&1); then
  log "PREFLIGHT FAIL — $PFOUT"
  bump_fail "$PFOUT"
  exit 1
fi

START=$(date +%s)

# ── build ───────────────────────────────────────────────────────────────────
# --no-guard: the collapse guard compares against the previous build and is
# meant for a human-run daily refresh. On a 2-minute loop a single transient
# blip would latch the board to stale data until someone noticed. The real
# protection here is that a failed build never reaches the hash check below,
# so the last good deployment simply keeps serving.
if ! OUT=$(cd "$DIR" && python3 build_data.py --no-guard 2>&1); then
  log "BUILD FAILED — previous deployment still serving"
  printf '%s\n' "$OUT" | tail -5 >> "$LOG"
  bump_fail "build_data.py failed: $(printf '%s\n' "$OUT" | tail -1)"
  exit 1
fi

# A section that errored for every company means the build "succeeded" but the
# data is partial. Publishing that would quietly blank a section on a page
# people read balances off, so treat it as a failure.
if printf '%s\n' "$OUT" | grep -q 'FAILED'; then
  log "PARTIAL BUILD (a section failed) — not publishing"
  printf '%s\n' "$OUT" | grep 'FAILED' | head -4 >> "$LOG"
  bump_fail "partial build: $(printf '%s\n' "$OUT" | grep FAILED | head -1)"
  exit 1
fi

# ── change detection ────────────────────────────────────────────────────────
# build_data.py fingerprints the business data as it writes (generated_at,
# build_seconds and per-query timings excluded, since those move every run) and
# drops the digest in a one-line file. Reading that costs nothing; re-parsing
# the 10 MB document here to ask the same question cost ~10s of every tick.
HASH=$(cat "$SITE/.data.sha256" 2>/dev/null | tr -d '[:space:]')
if [ -z "$HASH" ]; then
  log "NO FINGERPRINT — build_data.py did not write .data.sha256; not publishing"
  bump_fail "no fingerprint written"
  exit 1
fi

PREV=$(cat "$STATE" 2>/dev/null || echo "")
ELAPSED=$(( $(date +%s) - START ))

if [ "$HASH" = "$PREV" ]; then
  clear_fail
  log "no change (${ELAPSED}s build)"
  exit 0
fi

# ── publish ─────────────────────────────────────────────────────────────────
# No Vercel involved: drop the verified files where accounts-data-serve.py
# serves them. cp-to-temp + mv keeps a reader from ever seeing a half-written
# data.json; rsync --delay-updates does the same for the v2 slice directory
# (every file lands as a temp name first, the renames happen together at the
# end, so manifest.json and the slices it describes flip as one).
if ! mkdir -p "$PUBROOT/v1" "$PUBROOT/v2" 2>/dev/null; then
  log "PUBLISH FAILED — cannot create $PUBROOT (previous data still serving)"
  bump_fail "PUBROOT not writable"
  exit 1
fi

if ! { cp "$SITE/data.json" "$PUBROOT/v1/.data.json.tmp" \
       && mv -f "$PUBROOT/v1/.data.json.tmp" "$PUBROOT/v1/data.json"; }; then
  log "PUBLISH FAILED — could not place v1 data.json (previous data still serving)"
  bump_fail "v1 publish copy failed"
  exit 1
fi

# ── v2 board ────────────────────────────────────────────────────────────────
# The same build, cut into per-page slices with derivations and an independent
# re-derivation of every headline. v2 failing must never hold up v1: v1's data
# is already live above, and any problem here is logged, not propagated.
V2NOTE=""
if [ -d "$DIR/../site-v2" ] && [ -f "$DIR/split_data.py" ]; then
  V2LOG=$( { python3 "$DIR/split_data.py" \
             && python3 "$DIR/derive.py" \
             && python3 "$DIR/verify.py" \
             && python3 "$DIR/history.py"; } 2>&1 ) && V2OK=1 || V2OK=0
  if [ "$V2OK" = "1" ]; then
    if rsync -a --delete --delay-updates "$DIR/../site-v2/data/" "$PUBROOT/v2/" 2>/dev/null; then
      # End-to-end: the PUBLIC page must hand back the build just written,
      # which proves the whole chain (Vercel rewrite → Traefik → this box).
      GEN_LOCAL=$(python3 -c "import json;print(json.load(open('$PUBROOT/v2/manifest.json')).get('generated_at',''))" 2>/dev/null || echo "?")
      GEN_LIVE=$(curl -s --max-time 20 "$V2URL/data/manifest.json" \
                 | python3 -c "import json,sys;print(json.load(sys.stdin).get('generated_at',''))" 2>/dev/null || echo "unreachable")
      if [ "$GEN_LIVE" = "$GEN_LOCAL" ]; then
        log "v2 PUBLISHED (live end-to-end) $(printf '%s' "$V2LOG" | grep -c 'DISAGREE' || true) disagreements"
      else
        V2NOTE=" v2 WARNING: live page returns '$GEN_LIVE', expected '$GEN_LOCAL' — rewrite/Traefik/serve chain?"
        log "v2 data placed but live check MISMATCH (live '$GEN_LIVE' vs local '$GEN_LOCAL')"
      fi
    else
      log "v2 PUBLISH FAILED — rsync into $PUBROOT/v2 (previous v2 data still serving)"
    fi
  else
    log "v2 BUILD FAILED (v1 is unaffected and still serving)"
    printf '%s\n' "$V2LOG" | tail -3 >> "$LOG"
  fi
fi

echo "$HASH" > "$STATE"
clear_fail
log "PUBLISHED (${ELAPSED}s build, VPS-served)$V2NOTE"
