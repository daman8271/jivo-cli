#!/usr/bin/env bash
# JIVO harness — Stop hook (post-turn learning check).
#
# Hermes forks a whole agent after every Nth turn to ask "did anything here
# deserve to be remembered?" (see harness/research/01-hermes-learning.md §2a).
# We keep the trigger and drop the fork: this just counts turns and raises a
# flag, which the next SessionStart surfaces to the agent already in the room.
#
# Silent and free. Exits 0 always.

set -u
HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Accounts runs Windows, where the interpreter is `python` (and `python3`
# is a Store stub that exits non-zero). Try each before giving up.
# On Windows `python3` is often a Microsoft Store stub: it EXISTS on PATH, so
# `command -v` finds it, but running it prints "Python was not found" and exits
# 9009. Verified on a real Accounts-class machine. So probe by EXECUTING a
# no-op, not by testing for presence. `python` first: it is the name that
# actually resolves to a real interpreter on Windows.
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "pass" >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
[ -z "$PY" ] && exit 0
"$PY" "$HARNESS_DIR/bin/harness.py" review >/dev/null 2>&1 || true

# Daily catch-up: pull main, restore the protected files, push this operator's
# own log. `run` no-ops after the first success each day, so putting it here
# costs one cheap date comparison per turn and needs no cron, no Task Scheduler,
# and no setup on the operator's machine — which is the point, because they
# cannot be asked to install one.
"$PY" "$HARNESS_DIR/bin/update.py" run >/dev/null 2>&1 || true
exit 0
