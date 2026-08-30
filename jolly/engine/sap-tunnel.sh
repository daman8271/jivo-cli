#!/usr/bin/env bash
# Bring up (and keep up) a local port that reaches SAP HANA when the direct
# DB ports are blocked.
#
# Why this exists: on 2026-08-11 the SAP box stopped answering on 30015 (HANA)
# and 50000 (Service Layer) from this Mac AND from the VPS, with no warning.
# SSH to the box still worked. Everything in jolly/ depends on HANA, so the
# tunnel is the reliable path, not the fallback.
#
# Route: this machine -> vps-pub -> VPS 127.0.0.1:47192 (SAP box's reverse
# tunnel) -> SAP box -> its own HANA on 30015.
#
#   ./jolly/engine/sap-tunnel.sh up      # open it, write a tunnelled hana.env
#   ./jolly/engine/sap-tunnel.sh check   # is HANA answering?
#   ./jolly/engine/sap-tunnel.sh down
#
# Then:  python3 jolly/engine/requirement.py --env "$(./jolly/engine/sap-tunnel.sh env)"

set -uo pipefail

LOCAL_PORT="${SAP_TUNNEL_PORT:-30016}"
SSH_HOST="${SAP_SSH_HOST:-jivo-sap-any}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_ENV="$REPO/connections/hana.env"
OUT_ENV="${SAP_TUNNEL_ENV:-$HOME/.jivo-hana-tunnel.env}"

write_env() {
  [ -f "$SRC_ENV" ] || { echo "missing $SRC_ENV" >&2; return 1; }
  sed -e "s/^HANA_HOST=.*/HANA_HOST=127.0.0.1/" \
      -e "s/^HANA_PORT=.*/HANA_PORT=$LOCAL_PORT/" "$SRC_ENV" > "$OUT_ENV"
  chmod 600 "$OUT_ENV"
}

port_open() { nc -z -w3 127.0.0.1 "$LOCAL_PORT" >/dev/null 2>&1; }

hana_ok() {
  "$REPO/hana-sql/hana-sql" -env "$OUT_ENV" "SELECT CURRENT_USER FROM DUMMY" 2>/dev/null \
    | grep -qv '^CURRENT_USER$'
}

case "${1:-up}" in
  up)
    write_env || exit 1
    if port_open; then echo "tunnel already up on $LOCAL_PORT"; exit 0; fi
    # -f backgrounds after auth; keepalives so a dead link is noticed, not hung on.
    ssh -f -N -o ExitOnForwardFailure=yes -o ConnectTimeout=15 \
        -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
        -L "$LOCAL_PORT:127.0.0.1:30015" "$SSH_HOST" </dev/null >/dev/null 2>&1
    for _ in $(seq 1 10); do port_open && break; done
    if port_open; then echo "tunnel up on $LOCAL_PORT -> $SSH_HOST:30015"; echo "env: $OUT_ENV"
    else echo "FAILED to open tunnel on $LOCAL_PORT" >&2; exit 1; fi
    ;;
  check)
    port_open || { echo "port $LOCAL_PORT closed"; exit 1; }
    if hana_ok; then echo "HANA answering through the tunnel"; else echo "port open but HANA not answering"; exit 1; fi
    ;;
  env)  echo "$OUT_ENV" ;;
  down) pkill -f "L $LOCAL_PORT:127.0.0.1:30015" && echo "tunnel closed" || echo "no tunnel running" ;;
  *)    echo "usage: $0 {up|check|env|down}" >&2; exit 2 ;;
esac
