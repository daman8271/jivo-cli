#!/usr/bin/env bash
# Idempotent "make sure the SAP bridge is up". Safe to call from anywhere, often,
# and concurrently — a lock keeps twenty miners from all rebuilding the tunnel at once.
#
#   13015 -> HANA           (VPS-parked 43015 -> hanadb:30015)
#   15000 -> Service Layer  (VPS-parked 45000 -> hanadb:50000)
#
# macOS has no flock(1), so the lock is a mkdir — atomic on every POSIX filesystem —
# with a staleness escape hatch so a killed holder cannot wedge the fleet forever.
set -uo pipefail
LOCKDIR=/tmp/jivo-sap-bridge.lock.d
QUIET=""; [ "${1:-}" = "-q" ] && QUIET=1

up() { nc -z -G 3 127.0.0.1 13015 >/dev/null 2>&1 && nc -z -G 3 127.0.0.1 15000 >/dev/null 2>&1; }
say() { [ -n "$QUIET" ] || echo "$@"; }

up && { say "bridge already up"; exit 0; }

acquired=""
for _ in $(seq 1 45); do
  if mkdir "$LOCKDIR" 2>/dev/null; then acquired=1; echo $$ > "$LOCKDIR/pid"; break; fi
  # a lock older than 90s belongs to a process that died mid-rebuild
  if [ -d "$LOCKDIR" ] && [ -z "$(find "$LOCKDIR" -maxdepth 0 -mmin -1.5 2>/dev/null)" ]; then
    rm -rf "$LOCKDIR" 2>/dev/null; continue
  fi
  sleep 2
  up && exit 0          # the holder fixed it for us
done
[ -n "$acquired" ] || { echo "bridge down; could not take the rebuild lock" >&2; exit 1; }
trap 'rm -rf "$LOCKDIR"' EXIT

up && exit 0

for p in 13015 15000; do lsof -ti :$p 2>/dev/null | xargs kill 2>/dev/null; done
sleep 1
ssh -N -f -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 \
    -o ConnectTimeout=12 -o BatchMode=yes \
    -L 13015:127.0.0.1:43015 -L 15000:127.0.0.1:45000 vps 2>/dev/null
for _ in $(seq 1 15); do sleep 1; up && { say "bridge rebuilt $(date +%H:%M:%S)"; exit 0; }; done
echo "bridge REBUILD FAILED $(date +%H:%M:%S)" >&2
exit 1
