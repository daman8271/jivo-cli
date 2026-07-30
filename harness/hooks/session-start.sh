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

# Accounts runs Windows, where the interpreter is `python` (and `python3`
# is a Store stub that exits non-zero). Try each before giving up.
PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -z "$PY" ] && exit 0
"$PY" "$HARNESS_DIR/bin/harness.py" context 2>/dev/null || true
exit 0
