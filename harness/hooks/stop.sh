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

command -v python3 >/dev/null 2>&1 || exit 0
python3 "$HARNESS_DIR/bin/harness.py" review >/dev/null 2>&1 || true
exit 0
