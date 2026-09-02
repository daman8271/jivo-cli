#!/usr/bin/env bash
# SAP office-bridge — reach the NEW SAP box (138.252.101.222) from HOME.
#
# WHY THIS EXISTS
# The new SAP Linux box 138.252.101.222 (hanadb) IP-filters its inbound: the
# JIVO OFFICE public IP is allowed, but home / the VPS are NOT (verified
# 2026-08-17: office PC reaches .222:22/30015/50000; home+VPS get nothing —
# ICMP and every TCP port dead). This mirrors the OLD box, which was also
# office-only and reached from home via a tunnel.
#
# THE ROUTE (same idea as the old jivo-sap-any):
#   this Mac → ssh vps → 127.0.0.1:23001 (Victus, an office PC parked on the VPS
#   reverse-tunnel) → 138.252.101.222 : {30015 HANA, 50000 Service Layer}
# Victus is whitelisted (it's in the office), so it does the final hop for us.
#
# Local ports this opens on the Mac:
#   13015 → .222:30015 (HANA SQL)     — use connections/hana-office-bridge.env
#   15000 → .222:50000 (Service Layer)— use SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000
#
# CAVEAT: depends on the office PC 'Victus' being powered on and parked on the
# VPS (FleetPanel: Victus green / tunnel :23001). If it sleeps, the bridge dies.
# The durable fix is a reverse tunnel FROM .222 itself to the VPS (autossh),
# exactly like the old box had — see new-servers.env. Until that's set up, this
# is the working path.
set -euo pipefail
JUMP_PORT="${JUMP_PORT:-23001}"      # Victus's parked sshd port on the VPS
JUMP_USER="${JUMP_USER:-prabh}"
SAP_HOST="${SAP_HOST:-138.252.101.222}"

# clear any stale local listeners
for p in 13015 15000; do lsof -ti :$p 2>/dev/null | xargs kill 2>/dev/null || true; done
pkill -f "${JUMP_PORT} ${JUMP_USER}" 2>/dev/null || true
sleep 1

echo "bringing up SAP office-bridge via Victus (:${JUMP_PORT}) → ${SAP_HOST} ..."
ssh -N -f \
  -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=4 -o ConnectTimeout=25 \
  -L 13015:${SAP_HOST}:30015 \
  -L 15000:${SAP_HOST}:50000 \
  -J vps -p ${JUMP_PORT} ${JUMP_USER}@127.0.0.1

sleep 4
ok=1
for p in 13015 15000; do
  if nc -z -G 4 127.0.0.1 $p 2>/dev/null; then echo "  ✅ 127.0.0.1:$p up"; else echo "  ✗ 127.0.0.1:$p FAILED"; ok=0; fi
done
[ $ok -eq 1 ] && echo "bridge up. HANA: hana-sql -env connections/hana-office-bridge.env  |  SAP: SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 sapb1 ..."
exit $((1-ok))
