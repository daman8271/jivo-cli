#!/usr/bin/env bash
# loop.sh — ONE Mark 3 ingest cycle. This is what cron calls every 3 minutes.
#
#   */3 * * * * /root/jivo-courier/jolly/live/loop.sh
#
# It does three things and nothing else:
#   1. refuses to overlap — a cycle that overruns its slot is never doubled up
#      (two collectors against these servers is the retry storm we must not cause)
#   2. runs live/collect.py once
#   3. appends a stamped line-by-line log to live/state/loop.log, rotating at 5 MB
#
# Exit code is collect.py's own: 0 = at least one source answered, 1 = every
# source failed, 75 (EX_TEMPFAIL) = another cycle still holds the lock.
#
# Env passthrough: everything collect.py honours (MARK3_HEAVY_EVERY_S,
# MARK3_FORCE_HEAVY, MARK3_ONLY, MARK3_SKIP, …) works here unchanged.
# Loop-only knobs: LOOP_MAX_LOG_BYTES (default 5 MiB), LOOP_KEEP (default 3
# rotated files), LOOP_TIMEOUT_S (default 175 — under the 180 s slot).

set -uo pipefail

LIVE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
JOLLY_DIR="$(dirname -- "$LIVE_DIR")"
STATE_DIR="${MARK3_STATE_DIR:-$LIVE_DIR/state}"
LOG="$STATE_DIR/loop.log"
LOCK="$STATE_DIR/.loop.lock"
MAX_BYTES="${LOOP_MAX_LOG_BYTES:-5242880}"      # 5 MiB
KEEP="${LOOP_KEEP:-3}"
TIMEOUT_S="${LOOP_TIMEOUT_S:-175}"
PY="${MARK3_PYTHON:-python3}"

mkdir -p "$STATE_DIR"

stamp() { date +'%Y-%m-%dT%H:%M:%S%z'; }
say()   { printf '%s %s\n' "$(stamp)" "$*" >>"$LOG"; }

# --- rotate BEFORE writing, so the cap is a real cap ------------------------
rotate() {
  local size
  size=$(wc -c <"$LOG" 2>/dev/null | tr -d ' ') || size=0
  [ -n "$size" ] || size=0
  if [ "$size" -ge "$MAX_BYTES" ]; then
    local i
    for (( i=KEEP-1; i>=1; i-- )); do
      [ -f "$LOG.$i" ] && mv -f "$LOG.$i" "$LOG.$((i+1))"
    done
    mv -f "$LOG" "$LOG.1"
    : >"$LOG"
    say "log rotated at ${size} bytes (keeping $KEEP)"
  fi
}
[ -f "$LOG" ] || : >"$LOG"
rotate

# --- the one cycle ----------------------------------------------------------
run_cycle() {
  local rc=0 t0 t1
  t0=$(date +%s)
  say "---- cycle start (pid $$) ----"

  # Bound the whole cycle so a wedged CLI cannot eat the next slot. collect.py
  # has its own softer deadline (MARK3_ADAPTER_TIMEOUT_S); this is the hard one.
  # `timeout` is GNU coreutils — present on the VPS, absent on stock macOS, so
  # its absence just means we rely on collect.py's own deadline.
  if command -v timeout >/dev/null 2>&1; then
    timeout -k 10 "$TIMEOUT_S" "$PY" "$LIVE_DIR/collect.py" >>"$LOG" 2>&1
    rc=$?
    [ "$rc" -eq 124 ] && say "!! cycle KILLED by timeout after ${TIMEOUT_S}s"
  else
    "$PY" "$LIVE_DIR/collect.py" >>"$LOG" 2>&1
    rc=$?
  fi

  t1=$(date +%s)
  say "---- cycle end rc=$rc in $((t1 - t0))s ----"
  return "$rc"
}

# --- no overlap, ever -------------------------------------------------------
# flock is the real mechanism and it is what runs on the VPS. macOS ships no
# flock(1), so there is an atomic-mkdir fallback for local testing; it breaks a
# lock only when its recorded pid is provably gone.
if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK"
  if ! flock -n 9; then
    say "SKIP — previous cycle still running (flock held)"
    exit 75
  fi
  echo "$$" >&9 2>/dev/null || true
  run_cycle
  exit $?
fi

LOCKDIR="$STATE_DIR/.loop.lockd"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  prev=$(cat "$LOCKDIR/pid" 2>/dev/null || echo "")
  if [ -n "$prev" ] && kill -0 "$prev" 2>/dev/null; then
    say "SKIP — previous cycle still running (pid $prev)"
    exit 75
  fi
  say "breaking stale lock (pid '${prev:-unknown}' is gone)"
  rm -rf "$LOCKDIR"
  mkdir "$LOCKDIR" 2>/dev/null || { say "SKIP — could not take lock"; exit 75; }
fi
echo "$$" >"$LOCKDIR/pid"
trap 'rm -rf "$LOCKDIR"' EXIT INT TERM
run_cycle
exit $?
