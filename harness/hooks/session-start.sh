#!/usr/bin/env bash
# JIVO harness — SessionStart hook.
#
# Injects the persona-filtered corrections digest into every session, so a
# correction one operator recorded reaches every other operator's Claude.
#
# Fails silently and exits 0 always: a broken harness must never stop someone
# from doing their job.

set -u
HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v python3 >/dev/null 2>&1 || exit 0
python3 "$HARNESS_DIR/bin/harness.py" context 2>/dev/null || true
exit 0
