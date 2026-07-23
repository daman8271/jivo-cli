#!/usr/bin/env bash
# =============================================================================
# factory_daily.sh — the FULL daily chain (cron entrypoint).
#   1. factory_refresh.sh : rotating-auth -> full capture -> render fresh vault
#   2. jivo-data-bank/daily_rebuild.sh : fuse jivo+ecom+factory, fail-closed
#      verify, deterministic full REPLACE, commit (git history = time machine)
#   3. optional auto-push (off by default; export FACTORY_AUTOPUSH=1 to enable)
#
# Fail-closed: a refresh/capture/render failure stops before the data bank is
# touched; a verify failure inside daily_rebuild aborts WITHOUT committing.
# =============================================================================
set -uo pipefail
LOG="${FACTORY_DAILY_LOG:-/root/jivo-factory-intel/daily.log}"
ts(){ date -u +%Y-%m-%dT%H:%M:%SZ; }
log(){ echo "[$(ts)] $*" | tee -a "$LOG"; }

log "=== factory_daily START ==="

# 1. refresh the factory source vault
if ! /root/jivo-factory-intel/bin/factory_refresh.sh >>"$LOG" 2>&1; then
  log "factory_refresh FAILED (rc=$?) — data bank NOT rebuilt"; exit 1
fi

# 2. fuse into the data bank (jivo + ecom + factory) + fail-closed verify + commit
if ! JDB_SEMANTIC=auto bash /root/jivo-data-bank/bin/daily_rebuild.sh >>"$LOG" 2>&1; then
  log "daily_rebuild FAILED/aborted (rc=$?) — no bad commit (fail-closed)"; exit 2
fi

# 3. optional: push the proprietary data bank to GitHub (default OFF)
if [ "${FACTORY_AUTOPUSH:-0}" = "1" ]; then
  if (cd /root/jivo-data-bank && git push origin main) >>"$LOG" 2>&1; then
    log "pushed to origin/main"
  else
    log "push FAILED (will retry next run)"
  fi
else
  log "auto-push OFF — owner pushes: ! cd /root/jivo-data-bank && git push origin main"
fi

log "=== factory_daily DONE ==="
