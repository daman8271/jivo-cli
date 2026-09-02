#!/bin/bash
# freshness-watchdog.sh — the guarantee that does not depend on the build.
#
# live-refresh.sh can only tell you it failed if it runs. On 2026-08-22 it ran
# every two minutes and failed every time, for five hours, and the board kept
# serving 13:42 numbers as though they were live. Nothing was watching the thing
# the operator actually sees.
#
# This watches THAT: it fetches the deployed page's own data and asks how old the
# numbers on it are. It has no dependency on hana-sql, on HANA, on the build, or
# on the deploy — so it survives every failure mode that hid the freeze.
#
# Install (VPS):  */15 * * * * /root/jivo-cli/accounts-dashboard/pipeline/freshness-watchdog.sh
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/freshness-watchdog.log"
URL="${WATCH_URL:-https://jivo-accounts.vercel.app}"
MAX_MIN="${MAX_STALE_MIN:-30}"
ACTIVE_FROM="${ACTIVE_FROM:-7}"
ACTIVE_TO="${ACTIVE_TO:-23}"

log() { printf '%s %s\n' "$(date '+%F %T %Z')" "$*" >> "$LOG"; }

H=$(TZ=Asia/Kolkata date +%-H)
[ "$H" -ge "$ACTIVE_FROM" ] && [ "$H" -lt "$ACTIVE_TO" ] || exit 0   # don't cry wolf overnight

# Prefer the small manifest (v2); fall back to the monolith (v1).
STAMP=""
for path in "/data/manifest.json" "/data.json"; do
  BODY=$(curl -s --max-time 25 "${URL}${path}?t=$(date +%s)" 2>/dev/null) || continue
  [ -n "$BODY" ] || continue
  STAMP=$(printf '%s' "$BODY" | python3 -c '
import sys, json
try:
    print(json.load(sys.stdin).get("generated_at", ""))
except Exception:
    pass' 2>/dev/null)
  [ -n "$STAMP" ] && break
done

if [ -z "$STAMP" ]; then
  log "UNREACHABLE — could not read generated_at from $URL"
  "$DIR/notify-fleet.sh" "Accounts Board unreachable: no generated_at from $URL"
  exit 1
fi

AGE_MIN=$(python3 -c '
import sys, datetime
t = datetime.datetime.fromisoformat(sys.argv[1])
now = datetime.datetime.now(t.tzinfo)
print(int((now - t).total_seconds() // 60))' "$STAMP" 2>/dev/null || echo 9999)

if [ "$AGE_MIN" -gt "$MAX_MIN" ]; then
  log "STALE — board is serving data ${AGE_MIN} min old (limit ${MAX_MIN}); generated_at=$STAMP"
  TAIL=$(tail -3 "$DIR/live-refresh.log" 2>/dev/null | tr '\n' ' | ')
  "$DIR/notify-fleet.sh" "Accounts Board STALE: ${AGE_MIN} min old (limit ${MAX_MIN}). Last log: ${TAIL}"
  exit 2
fi

log "fresh (${AGE_MIN} min)"
