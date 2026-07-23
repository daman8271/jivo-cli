#!/usr/bin/env bash
# =============================================================================
# factory_refresh.sh — daily refresh of the Jivo Mart factory SOURCE vault.
#
# Self-sustaining auth (rotating refresh token) -> full lossless capture
# (152 paginated endpoints + the gap endpoints, caps busted) -> deterministic
# full REPLACE render of vault/. This is the factory's "scraper" equivalent
# (like ecom-intel's daily crawl). It does NOT touch the data bank; the
# data-bank daily_rebuild.sh fuses the fresh vault afterwards (factory_pillar.py).
# =============================================================================
set -euo pipefail
ROOT=/root/jivo-factory-intel
LOG="${FACTORY_REFRESH_LOG:-$ROOT/refresh.log}"
ts(){ date -u +%Y-%m-%dT%H:%M:%SZ; }
log(){ echo "[$(ts)] $*" | tee -a "$LOG" >&2; }
alert(){ log "ABORT: $*"; [ -x /root/.claude/hooks/notify.sh ] && /root/.claude/hooks/notify.sh "JIVO factory refresh ABORTED: $*" >/dev/null 2>&1 || true; }

# single-flight lock
exec 9>"$ROOT/.refresh.lock"
flock -n 9 || { log "another refresh holds the lock; exiting"; exit 0; }

log "=== factory_refresh start ==="

# 1. keep the JWT alive (rotating refresh token; self-sustaining within ~7d).
# Tolerate a failed refresh as long as the access token still works (~25h grace);
# hard-fail only when access is ALSO dead. Either way, alert the owner to re-seed.
if ! python3 "$ROOT/bin/refresh_token.py" >>"$LOG" 2>&1; then
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 \
    -H "Authorization: Bearer $(cat "$HOME/.config/jivo-factory/access.jwt" 2>/dev/null)" \
    -H "Company-Code: JIVO_MART" https://factory.jivo.in/api/v1/accounts/me/ 2>/dev/null || echo 000)
  if [ "$CODE" = "200" ]; then
    log "WARN: token refresh failed but access still valid — capturing today; OWNER re-seed soon: JIVO_FACTORY_EMAIL=.. JIVO_FACTORY_PASSWORD=.. bash $ROOT/bin/reseed.sh"
  else
    alert "auth dead (refresh failed + access HTTP $CODE). Owner re-seed: JIVO_FACTORY_EMAIL=.. JIVO_FACTORY_PASSWORD=.. bash $ROOT/bin/reseed.sh"; exit 2
  fi
fi

# 2. full lossless capture (overwrites raw/)
python3 "$ROOT/bin/capture.py"      >>"$LOG" 2>&1 || { alert "capture.py FAILED";      exit 3; }
python3 "$ROOT/bin/capture_gaps.py" >>"$LOG" 2>&1 || { alert "capture_gaps.py FAILED"; exit 4; }

# 3. deterministic full REPLACE of the source vault
python3 "$ROOT/bin/render.py"       >>"$LOG" 2>&1 || { alert "render.py FAILED";       exit 5; }

N=$(find "$ROOT/vault" -name '*.md' | wc -l | tr -d ' ')
R=$(python3 -c "import json;m=json.load(open('$ROOT/raw/_manifest.json'));print(sum(v.get('count',0) for v in m.values() if v.get('kind') in ('list','paginated_list')))" 2>/dev/null || echo '?')
log "=== factory_refresh done: vault=$N notes, ~$R captured records ==="

# --- eager today/ hook (instant-per-source rule): publish factory's slice into
# the data-bank today/ the moment its vault is refreshed. Self-gates on readiness
# + no-ops if unchanged; never blocks or fails this refresh. ---
/opt/ecom-intel/bin/advance_today_section.sh factory >> /opt/ecom-intel/bin/build_today.log 2>&1 || true
