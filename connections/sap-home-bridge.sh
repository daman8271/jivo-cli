#!/usr/bin/env bash
# SAP home-bridge (24/7, DURABLE) — reach the new SAP box from ANY machine.
#
# The new SAP Linux box (hanadb, 138.252.101.222) IP-filters inbound to the
# office only. To reach it from home/VPS/anywhere, the box itself dials OUT to
# our VPS every minute (cron guard + ~/vps-tunnel.sh on the box) and parks:
#     VPS 127.0.0.1:47522 -> hanadb:22    (SSH)
#     VPS 127.0.0.1:43015 -> hanadb:30015 (HANA)
#     VPS 127.0.0.1:45000 -> hanadb:50000 (Service Layer)
# This is the SAME mechanism the old box used (jivo-sap-any). It does NOT depend
# on any office PC being on — only the always-on VPS + the always-on server.
#
# This script just forwards those VPS-parked ports to local ports on THIS machine:
#     localhost:13015 -> HANA   (use connections/hana-office-bridge.env)
#     localhost:15000 -> SL     (SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 sapb1 ...)
# For a shell on the box:  ssh jivo-sap-new
set -euo pipefail
for p in 13015 15000; do lsof -ti :$p 2>/dev/null | xargs kill 2>/dev/null || true; done
sleep 1
echo "bringing up SAP home-bridge via VPS (parked hanadb ports) ..."
ssh -N -f -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=4 \
  -L 13015:127.0.0.1:43015 \
  -L 15000:127.0.0.1:45000 \
  vps
sleep 3
ok=1
for p in 13015 15000; do
  if nc -z -G 4 127.0.0.1 $p 2>/dev/null; then echo "  ✅ 127.0.0.1:$p up"; else echo "  ✗ 127.0.0.1:$p FAILED"; ok=0; fi
done
[ $ok -eq 1 ] && echo "bridge up. HANA: hana-sql -env connections/hana-office-bridge.env  |  SAP: SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 sapb1 ..."
exit $((1-ok))
