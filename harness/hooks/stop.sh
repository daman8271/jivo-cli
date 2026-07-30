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
PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -z "$PY" ] && exit 0
"$PY" "$HARNESS_DIR/bin/harness.py" review >/dev/null 2>&1 || true
exit 0
