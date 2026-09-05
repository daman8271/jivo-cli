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
#        gen_live.py     -> live/state/plan/*.json (its cross-checks are the gate)
#        publish         -> a last look over live/state/plan/*.json, then a SWEEP of
#                           anything there that is not in this cycle's manifest.json
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
# gen_live.py writes straight into $PLAN_DIR — atomically, days/ included — so by the
# time the publish step runs there is nothing left to copy. SITE_DATA therefore points
# AT the published directory: publish_plan becomes a last look that this cycle's files
# are there and readable, and, the reason this line changed, it can no longer copy
# site-sep/data (the FROZEN 31-August Mark 2 plan) straight over the live one.
SITE_DATA="$PLAN_DIR"
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

# Copy the generated plan JSON where the publisher can reach it, then SWEEP.
#
# Per file: write a .tmp beside the target and mv it into place, because
# state_server.py is serving this directory while we write and half a JSON file is
# worse than yesterday's whole one.
#
# THE SWEEP. gen_live.py writes plan/manifest.json — the exact list of files it just
# produced, days included. Anything else in plan/ or plan/days/ is from another
# vintage, and it was not harmless: build.json, questions.json, scenarios.json and
# whatsapp.json were Mark 2 files that nothing had generated for days, and every cycle
# re-copied them and re-stamped their mtime so they looked as fresh as the real plan
# while the site served them. They are deleted here, one log line each.
#
# The manifest is the ONLY authority for the sweep. No manifest, no sweep — a missing
# or unreadable manifest leaves every file exactly where it is and says so, because
# the one thing worse than serving a stale file is deleting a live one on a guess.
# manifest.json lists itself, so it survives its own sweep.
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
  "$PY" - "$PLAN_DIR" <<'SWEEP' || rc=1
import glob, json, os, sys
plan = sys.argv[1]
mpath = os.path.join(plan, "manifest.json")
try:
    with open(mpath, encoding="utf-8") as fh:
        m = json.load(fh)
    keep_top = set(m["files"]) | {"manifest.json"}
    keep_days = set(m["days"])
except (OSError, ValueError, KeyError, TypeError) as e:
    print(f"publish_plan: no usable {mpath} ({e}) — NOTHING swept. Every file in "
          f"{plan} stays where it is; a sweep without a manifest is a guess.")
    raise SystemExit(0)
gone = []
for path in sorted(glob.glob(os.path.join(plan, "*.json"))):
    if os.path.basename(path) not in keep_top:
        try:
            os.remove(path)
            gone.append(os.path.basename(path))
        except OSError as e:
            print(f"publish_plan: could not delete {os.path.basename(path)}: {e}")
for path in sorted(glob.glob(os.path.join(plan, "days", "*.json"))):
    if os.path.basename(path) not in keep_days:
        try:
            os.remove(path)
            gone.append("days/" + os.path.basename(path))
        except OSError as e:
            print(f"publish_plan: could not delete days/{os.path.basename(path)}: {e}")
for name in gone:
    print(f"publish_plan: DELETED {name} — not in this cycle's manifest.json, so it was "
          f"a leftover being served as though it were part of the plan")
print(f"publish_plan: swept {plan} against manifest.json — "
      f"{len(gone)} deleted, {len(keep_top)} + {len(keep_days)} day file(s) kept")
SWEEP
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
    CHAIN_STEP=freeze
    return 1
  }
  # env(1), not a `VAR=x func` prefix: an assignment in front of a FUNCTION call
  # lands in the current shell rather than cleanly in the child's environment.
  # This is also verbatim the invocation live/PHASE4-FREEZE-LIVE.md specifies.
  # The horizon shrinks by a day every day; the engine rewrites day-01..day-N but never
  # deletes yesterday's day-N+1, and gen_live refuses on "28 files / 27 days" (bit us 2026-09-04).
  rm -f "$JOLLY_DIR/sim/days-live/day-"*.json 2>/dev/null || true
  run_step sim env SIM_INPUTS=sim/live-inputs.json SIM_TAG=-live \
    "$PY" "$JOLLY_DIR/engine/august_sim.py" || {
    say "chain STOPPED at sim — no new sim/days-live; the site keeps its last plan."
    CHAIN_STEP=sim
    return 1
  }
  run_step gen "$PY" "$LIVE_DIR/gen_live.py" || {
    say "chain STOPPED at gen — gen_live.py refused to write (its cross-checks are ""the gate and a failing check is a wrong number, never a check to weaken). ""live/state/plan/ keeps its last good copy."
    CHAIN_STEP=gen
    return 1
  }
  # Is what is now published actually THIS cycle's re-plan? It used to be a standing
  # warning: gen-data.py is hard-wired to the `-sep` artifacts, so it re-emitted the
  # 31-AUGUST FROZEN September plan every cycle wearing today's timestamp. gen_live.py
  # reads the `-live` artifacts, so the two should agree now — and this became a real
  # check instead of a notice. It compares the freeze against the PUBLISHED file, on
  # the collection stamp as well as the dates: the dates are the same all day, the
  # stamp changes every cycle, so only the stamp catches "gen_live.py quietly wrote
  # nothing". STILL LOG ONLY — it never fails the chain, because state.json is already
  # out and a mismatch is a thing to read in the log, not a reason to kill the loop.
  "$PY" - "$JOLLY_DIR" "$PLAN_DIR" <<'EOF' >>"$LOG" 2>&1 || true
import json, os, sys
jolly, plan_dir = sys.argv[1], sys.argv[2]
try:
    frozen = json.load(open(os.path.join(jolly, "sim", "live-inputs.json")))["meta"]
    shown = json.load(open(os.path.join(plan_dir, "overview.json")))["meta"]
except Exception as e:
    print(f"  chain: could not compare the published plan with this cycle's freeze ({e})")
else:
    want = (frozen["horizon"], frozen.get("state_collected_at") or frozen["as_of"])
    got = (shown.get("horizon"), shown.get("collected_at"))
    if want != got:
        print(f"  !! chain: THE PUBLISHED PLAN IS NOT THIS CYCLE'S — plan/overview.json says "
              f"{got} against this cycle's freeze {want}. gen_live.py wrote nothing, or "
              f"something else overwrote live/state/plan/.")
    else:
        print(f"  chain: published plan {got[0]} as of {got[1]} matches this cycle's freeze")
EOF
  run_step publish publish_plan || {
    say "chain STOPPED at publish — live/state/plan/ keeps its last good copy."
    CHAIN_STEP=publish
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
    CHAIN_STEP=""
    run_chain || crc0=$?
    "$PY" "$LIVE_DIR/chain_status.py" "$STATE_DIR" "$crc0" "$CHAIN_STEP" >>"$LOG" 2>&1 || true
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
  CHAIN_STEP=""
  run_chain || crc=$?
  # chain.json + the alarm: the loop's rc never carries the chain's outcome, so this
  # is the only place a 14-hour plan freeze (4 Sep 21:36) becomes visible anywhere.
  "$PY" "$LIVE_DIR/chain_status.py" "$STATE_DIR" "$crc" "$CHAIN_STEP" >>"$LOG" 2>&1 || true

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
