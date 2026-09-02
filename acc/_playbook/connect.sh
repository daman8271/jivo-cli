#!/usr/bin/env bash
# Get this shell SAP-ready from anywhere (home, VPS, office).
# USAGE:  source acc/_playbook/connect.sh [operator-env]
#   e.g.  source acc/_playbook/connect.sh navdeep-user36.env
# Sourcing matters — the exports must survive into your shell.

_ae_repo="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
_ae_env="${1:-navdeep-user36.env}"

# 1. operator login — sourced FIRST so the route chosen below wins over any host in the file
set -a; . "$_ae_repo/sap-b1/cli/$_ae_env" 2>/dev/null; set +a

# 2. route. Office boxes (and any whitelisted IP) reach SAP directly; only stand up
#    the bridge when they cannot. Forcing the bridge unconditionally breaks every
#    in-office machine, which has no fleet ssh route to build one with.
_ae_direct=138.252.101.222
if (exec 3<>/dev/tcp/$_ae_direct/50000) 2>/dev/null; then
  export SAPB1_HOST=$_ae_direct SAPB1_PORT=50000 SAPB1_TIMEOUT=180
  export HANA_ENV="$_ae_repo/connections/hana.env"
  echo "route: DIRECT $_ae_direct:50000 (no bridge needed)"
else
  if ! nc -z 127.0.0.1 15000 2>/dev/null; then
    bash "$_ae_repo/connections/sap-home-bridge.sh" || return 1 2>/dev/null || exit 1
  fi
  export SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 SAPB1_TIMEOUT=180
  export HANA_ENV="$_ae_repo/connections/hana-office-bridge.env"
  echo "route: BRIDGE 127.0.0.1:15000"
fi
export SAPB1_WRITE_LOG="$_ae_repo/queries/${SAPB1_USER:-unknown}/sap-writes.jsonl"
mkdir -p "$(dirname "$SAPB1_WRITE_LOG")"

echo "SAP ready · login=${SAPB1_USER:-?} · company=${SAPB1_COMPANYDB:-JIVO_OIL_HANADB} · route=$SAPB1_HOST:$SAPB1_PORT"
echo "write log -> $SAPB1_WRITE_LOG"
echo "verify:  (cd $_ae_repo/sap-b1/cli && ./sapb1 doctor)"
