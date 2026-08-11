#!/usr/bin/env bash
# ============================================================================
#  hermes-tmp-gc.sh — hourly. Stops the hermes container leaking the VPS disk.
#
#  On 2026-08-11 the VPS root filesystem was found 100% full (0 bytes free).
#  Cause: 39,671 abandoned `/tmp/tirith-install-*` directories inside the
#  `hermes` container, 8.5 MB each — ~36 GB. Hermes' installer creates one per
#  run and never removes it, so the leak is unbounded and silent until the disk
#  dies and every service on the box starts failing at once.
#
#  This is a MITIGATION, not a fix: the leak is upstream in hermes. If a hermes
#  upgrade ever stops creating these, this script simply finds nothing.
#
#  Only touches directories matching the exact leak pattern and untouched for
#  120+ minutes, so a genuinely in-flight install is never pulled out from
#  under itself.
# ============================================================================
set -u

LOG=/root/hermes-tmp-gc.log
TS=$(date '+%Y-%m-%d %H:%M:%S')

docker ps --format '{{.Names}}' 2>/dev/null | grep -qx hermes || exit 0

# `grep -c` EXITS 1 when the count is zero, so a trailing `|| echo 0` fires on
# the healthy path too and yields "0\n0" — which then blows up the arithmetic.
# Swallow the exit status inside the container instead, and default in the shell.
count_leaked() {
  docker exec hermes sh -c 'ls /tmp 2>/dev/null | grep -c "^tirith-install-" || true' 2>/dev/null | tr -dc '0-9'
}

before=$(count_leaked); before=${before:-0}
docker exec hermes sh -c \
  'find /tmp -maxdepth 1 -type d -name "tirith-install-*" -mmin +120 -exec rm -rf {} + 2>/dev/null' \
  >/dev/null 2>&1
after=$(count_leaked); after=${after:-0}

removed=$(( before - after ))
[ "$removed" -gt 0 ] && echo "$TS removed=$removed remaining=$after disk=$(df --output=pcent / | tail -1 | tr -d ' ')" >> "$LOG"

tail -n 500 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
exit 0
