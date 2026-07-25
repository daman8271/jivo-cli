#!/bin/bash
# TankhaPay daily login auto-refresh (v2, hardened per Atlas design review).
#
# Mints a fresh 24h JWT via `tankhapay-portal auth login` and caches it so the CLI
# (and any automated reads) never hit a stale/expired token. Belt-and-suspenders on
# top of the CLI's own auto-re-login-on-401. READ-ONLY: the only network call is the
# login token exchange.
#
# Invoked by LaunchAgent com.jivo.tankhapay-login-refresh (09:10 + 21:10 + on load/wake).
# Idempotent: a freshness gate makes RunAtLoad / coalesced wake-fires / manual kicks
# no-ops when the token is already fresh, so we hit the portal ~2×/day steady-state.
#
# SECRET HYGIENE: never `set -x`, never source .env, never log the password / its md5 /
# the JWT / the body key. Only success/failure, token validity, and the CLI's own
# secret-free banner are logged.

set -uo pipefail

PROJ="$HOME/jivo-cli/portals/tankhapay"
BIN="${TP_BIN_OVERRIDE:-$HOME/go/bin/tankhapay-portal}"   # override only for tests
ENV_FILE="$PROJ/.env"
LOG_DIR="$PROJ/logs"
LOG="$LOG_DIR/login-refresh.log"
TOKEN_JSON="$HOME/Library/Application Support/tankhapay-portal/token.json"

FRESH_S=36000     # <10h old  -> skip (already fresh)
STALE_S=93600     # >26h old  -> alert (refresh has been silently failing)
RETRY_SLEEP="${TP_RETRY_SLEEP:-60}"
FORCE=0; [ "${1:-}" = "--force" ] && FORCE=1

# launchd agents get a minimal env and no shell profile — set PATH explicitly.
export PATH="$HOME/go/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

mkdir -p "$LOG_DIR"
ts() { date '+%Y-%m-%dT%H:%M:%S%z'; }
log() { echo "$(ts) $*" >> "$LOG"; }

# Fire a Telegram alert if creds are present in .env (grep, never source). Degrades
# gracefully: missing creds -> log ALERT_SKIPPED and continue; alert curl failure is
# swallowed so it can never fail the run.
alert() {
  local msg="$1" tok chat
  tok="$(grep -E '^TG_ALERT_BOT_TOKEN=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2-)"
  chat="$(grep -E '^TG_ALERT_CHAT_ID='  "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2-)"
  if [ -z "$tok" ] || [ -z "$chat" ]; then
    log "ALERT_SKIPPED (no TG creds in .env)"; return 0
  fi
  curl -s -m 15 -o /dev/null \
    "https://api.telegram.org/bot${tok}/sendMessage" \
    --data-urlencode "chat_id=${chat}" \
    --data-urlencode "text=🔴 TankhaPay token refresh: ${msg}" || true
}

# a. Trim own log first (launchd appends forever; user-level newsyslog needs root).
if [ -f "$LOG" ] && [ "$(wc -c < "$LOG")" -gt 204800 ]; then
  tail -n 400 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
fi

# Preconditions.
[ -x "$BIN" ]      || { log "REFRESH_FAIL binary missing at $BIN"; exit 1; }
[ -f "$ENV_FILE" ] || { log "REFRESH_FAIL .env missing at $ENV_FILE"; exit 1; }
cd "$PROJ" || { log "REFRESH_FAIL cannot cd $PROJ"; exit 1; }

# Token age (missing file => infinitely old).
if [ -f "$TOKEN_JSON" ]; then
  AGE=$(( $(date +%s) - $(stat -f %m "$TOKEN_JSON") ))
else
  AGE=999999999
fi

# b. Staleness alarm — token older than 26h means refresh has been failing/skipped.
if [ "$AGE" -gt "$STALE_S" ]; then
  log "STALE age=${AGE}s (>26h) — refreshing now and alerting"
  alert "cached token was ${AGE}s old (>26h) — automated reads were about to go stale"
fi

# c. Freshness gate — skip if recently refreshed (keeps portal logins to ~2/day).
if [ "$FORCE" -eq 0 ] && [ "$AGE" -lt "$FRESH_S" ]; then
  log "SKIP_FRESH age=${AGE}s (<10h)"
  exit 0
fi

# d. Forced login with one retry (noise filter before alerting).
run_login() { "$BIN" auth login 2>&1; }
if out="$(run_login)"; then
  log "REFRESH_OK ${out//$'\n'/ }"
  exit 0
fi
sleep "$RETRY_SLEEP"
if out="$(run_login)"; then
  log "REFRESH_OK (retry) ${out//$'\n'/ }"
  exit 0
fi

# e. Double failure — the login path itself is broken; make it LOUD.
log "REFRESH_FAIL attempt=2 err=${out//$'\n'/ }"
alert "login failed twice — ${out//$'\n'/ }"
exit 1
