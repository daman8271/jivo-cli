#!/usr/bin/env bash
# Keep the SAP bridge alive for the length of a long mining run.
# Checks every 20s; rebuilds on the spot; appends a one-line audit trail.
BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${1:-/tmp/jivo-bridge-watchdog.log}"
echo "$(date '+%F %T')  watchdog start (pid $$)" >> "$LOG"
while :; do
  if ! (nc -z -G 3 127.0.0.1 13015 && nc -z -G 3 127.0.0.1 15000) >/dev/null 2>&1; then
    echo "$(date '+%F %T')  bridge DOWN -> rebuilding" >> "$LOG"
    bash "$BIN/bridge.sh" -q >> "$LOG" 2>&1 \
      && echo "$(date '+%F %T')  bridge back up" >> "$LOG" \
      || echo "$(date '+%F %T')  rebuild FAILED" >> "$LOG"
  fi
  sleep 20
done
