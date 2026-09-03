#!/usr/bin/env bash
# loop.sh — ONE Mark 3 ingest cycle. This is what cron calls every 3 minutes.
#
#   */3 * * * * /root/jivo-courier/jolly/live/loop.sh
#
# It does four things and nothing else:
#   1. refuses to overlap — a cycle that overruns its slot is never doubled up
#      (two collectors against these servers is the retry storm we must not cause)
#   2. runs live/collect.py once — this is the only step that touches the plant
#   3. runs the PLAN CHAIN on what collect just wrote:
#        freeze_live.py  -> sim/live-inputs.json   (the engine's input, from live state)
#        august_sim.py   -> sim/days-live/, summary-live.json, events-live.json
#        gen-data.py     -> site-sep/data/*.json   (its cross-checks are the gate)
#        publish         -> live/state/plan/*.json
#   4. appends a stamped line-by-line log to live/state/loop.log, rotating at 5 MB
#
# THE CHAIN NEVER COSTS THE INGEST ANYTHING. collect.py has already written
# state.json by the time step 3 starts, so a chain step that fails, or that runs
# out of budget, leaves the published live state exactly as collect left it. A
# failed step is logged and STOPS the rest of the chain (running the engine on a
# stale live-inputs.json would republish an old plan wearing today's timestamp),
# but it never changes what the ingest published and never changes the exit code.
#
# Exit code is collect.py's own: 0 = at least one source answered, 1 = every
# source failed, 75 (EX_TEMPFAIL) = another cycle still holds the lock. The chain
# does NOT move it — "the plant answered" and "the re-plan built" are different
# facts, and folding them together would make a gen-data refusal look like a dead
# ingest loop. The chain's outcome is a `chain ...` line in the log.
#
# THE WHOLE CYCLE, collect AND chain, stays inside LOOP_TIMEOUT_S. collect keeps
# its full budget; the chain gets whatever is left of it when collect returns, and
# any step with no budget left is logged SKIPPED rather than started.
#
# Env passthrough: everything collect.py honours (MARK3_HEAVY_EVERY_S,
# MARK3_FORCE_HEAVY, MARK3_FORCE_HOURLY, MARK3_ONLY, MARK3_SKIP, …) works here
# unchanged. Loop-only knobs: LOOP_MAX_LOG_BYTES (default 5 MiB), LOOP_KEEP
# (default 3 rotated files), LOOP_TIMEOUT_S (default 175 — under the 180 s slot),
# LOOP_SKIP_CHAIN=1 (collect only), LOOP_ONLY_CHAIN=1 (chain only, ZERO calls to the
# plant — re-runs the re-plan on the state already on disk), SIM_HOURS /
# SIM_SUNDAYS_OFF (the engine's own knobs, defaulted here to 12 h / Sundays off).

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
PLAN_DIR="$STATE_DIR/plan"
SITE_DATA="$JOLLY_DIR/site-sep/data"
SKIP_CHAIN="${LOOP_SKIP_CHAIN:-0}"
# LOOP_ONLY_CHAIN=1 re-runs the plan chain on the state.json ALREADY on disk and makes
# no call to the plant at all. It is how a change to the engine, the freeze or
# gen-data.py is tested without spending a live cycle on it.
ONLY_CHAIN="${LOOP_ONLY_CHAIN:-0}"
# The engine's own knobs. The baseline is 12 hours a day with Sundays off; a
# scenario cycle overrides them in the environment, it is not edited in here.
export SIM_HOURS="${SIM_HOURS:-12}"
export SIM_SUNDAYS_OFF="${SIM_SUNDAYS_OFF:-1}"

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

# --- one chain step ---------------------------------------------------------
# Times it, bounds it by whatever is LEFT of the cycle budget, logs the result,
# and returns its exit code. Never aborts the script: the caller decides.
# $1 = label, rest = argv. Runs from JOLLY_DIR — every path the engine and
# gen-data.py write is relative to it.
CHAIN_DEADLINE=0
run_step() {
  local label="$1"; shift
  local rc=0 s0 s1 left
  left=$(( CHAIN_DEADLINE - $(date +%s) ))
  if [ "$left" -le 2 ]; then
    say "  step $label SKIPPED — no budget left in this cycle's ${TIMEOUT_S}s"
    return 78
  fi
  s0=$(date +%s)
  # timeout(1) EXECS its argument, and a shell function is not a binary — it answers
  # rc=127 "No such file or directory". The only function step is publish_plan, a
  # local file copy that cannot hang on a network, so it runs bare inside the budget
  # check rather than being wrapped.
  if declare -F "$1" >/dev/null 2>&1; then
    ( cd "$JOLLY_DIR" && "$@" ) >>"$LOG" 2>&1
    rc=$?
  elif command -v timeout >/dev/null 2>&1; then
    ( cd "$JOLLY_DIR" && timeout -k 5 "$left" "$@" ) >>"$LOG" 2>&1
    rc=$?
    [ "$rc" -eq 124 ] && say "  !! step $label KILLED by timeout after ${left}s"
  else
    # macOS ships no timeout(1); the budget is then advisory and the step runs bare.
    ( cd "$JOLLY_DIR" && "$@" ) >>"$LOG" 2>&1
    rc=$?
  fi
  s1=$(date +%s)
  if [ "$rc" -eq 0 ]; then
    say "  step $label ok in $((s1 - s0))s"
  else
    say "  !! step $label FAILED rc=$rc in $((s1 - s0))s"
  fi
  return "$rc"
}

# Copy the generated plan JSON where the publisher can reach it. Per file:
# write a .tmp beside the target and mv it into place, because state_server.py
# is serving this directory while we write and half a JSON file is worse than
# yesterday's whole one.
publish_plan() {
  local n=0 rc=0 f base
  mkdir -p "$PLAN_DIR" || return 1
  for f in "$SITE_DATA"/*.json; do
    [ -f "$f" ] || continue                 # no nullglob: an unmatched glob stays literal
    base="$(basename "$f")"
    if cp -- "$f" "$PLAN_DIR/.$base.tmp" && mv -f -- "$PLAN_DIR/.$base.tmp" "$PLAN_DIR/$base"
    then n=$((n + 1))
    else echo "publish_plan: could not publish $base"; rc=1; rm -f -- "$PLAN_DIR/.$base.tmp"
    fi
  done
  if [ "$n" -eq 0 ]; then
    echo "publish_plan: no $SITE_DATA/*.json to copy"
    return 1
  fi
  echo "publish_plan: $n file(s) -> $PLAN_DIR"
  return "$rc"
}

# --- the plan chain ---------------------------------------------------------
# Runs only after collect.py has published state.json. Stops at the first
# failure; every later step is logged SKIPPED with the reason.
run_chain() {
  local rc=0
  if [ "$SKIP_CHAIN" = "1" ]; then
    say "chain SKIPPED — LOOP_SKIP_CHAIN=1"
    return 0
  fi
  say "chain start ($(( CHAIN_DEADLINE - $(date +%s) ))s of budget left)"

  run_step freeze "$PY" "$LIVE_DIR/freeze_live.py" || {
    say "chain STOPPED at freeze — sim/live-inputs.json was not rewritten, so the ""engine is not run on a stale one. state.json is published and unaffected."
    return 1
  }
  # env(1), not a `VAR=x func` prefix: an assignment in front of a FUNCTION call
  # lands in the current shell rather than cleanly in the child's environment.
  # This is also verbatim the invocation live/PHASE4-FREEZE-LIVE.md specifies.
  run_step sim env SIM_INPUTS=sim/live-inputs.json SIM_TAG=-live \
    "$PY" "$JOLLY_DIR/engine/august_sim.py" || {
    say "chain STOPPED at sim — no new sim/days-live; the site keeps its last plan."
    return 1
  }
  run_step gen "$PY" "$JOLLY_DIR/site-sep/scripts/gen-data.py" || {
    say "chain STOPPED at gen — gen-data.py refused to write (its cross-checks are ""the gate and a failing check is a wrong number, never a check to weaken). ""site-sep/data/ keeps its last good copy."
    return 1
  }
  # Is what we are about to publish actually THIS cycle's re-plan? gen-data.py reads
  # the `-sep` artifacts (sim/sep-inputs.json, sim/days-sep/, five -sep scenarios,
  # out/*-sep.json) and has no tag knob, so today it re-emits the 31-AUGUST FROZEN
  # September plan and the freeze/sim above are only a gate on it. Wiring it to `-live`
  # is Phase 5, not a flag. Until then this compares the two horizons and says so out
  # loud every cycle — a published plan wearing the wrong date must never be silent.
  # LOG ONLY: it never fails the chain, because publishing the frozen plan is, for now,
  # the intended behaviour.
  "$PY" - "$JOLLY_DIR" <<'EOF' >>"$LOG" 2>&1 || true
import json, os, sys
j = sys.argv[1]
try:
    live = json.load(open(os.path.join(j, "sim", "live-inputs.json")))["meta"]["horizon"]
    site = json.load(open(os.path.join(j, "site-sep", "data", "overview.json")))["meta"]["horizon"]
except Exception as e:
    print(f"  chain: could not compare horizons ({e})")
else:
    if live != site:
        print(f"  !! chain: PUBLISHING THE FROZEN PLAN, NOT THE LIVE ONE — "
              f"site-sep/data horizon {site} vs this cycle's freeze {live}. "
              f"gen-data.py is hard-wired to the -sep artifacts (Phase 5).")
    else:
        print(f"  chain: published plan horizon {site} matches this cycle's freeze")
EOF
  run_step publish publish_plan || {
    say "chain STOPPED at publish — live/state/plan/ keeps its last good copy."
    return 1
  }
  say "chain ok"
  return 0
}

# --- the one cycle ----------------------------------------------------------
run_cycle() {
  local rc=0 t0 t1
  t0=$(date +%s)
  CHAIN_DEADLINE=$((t0 + TIMEOUT_S))
  say "---- cycle start (pid $$) ----"

  if [ "$ONLY_CHAIN" = "1" ]; then
    say "collect SKIPPED — LOOP_ONLY_CHAIN=1; the chain re-runs on the state already on disk"
    local crc0=0
    run_chain || crc0=$?
    t1=$(date +%s)
    say "---- cycle end rc=0 chain=$crc0 in $((t1 - t0))s (collect skipped) ----"
    return 0
  fi

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

  # The chain runs on what collect just wrote, inside the REMAINING budget. Its
  # outcome never changes rc: state.json is already published either way.
  local crc=0
  run_chain || crc=$?

  t1=$(date +%s)
  say "---- cycle end rc=$rc chain=$crc in $((t1 - t0))s ----"
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
