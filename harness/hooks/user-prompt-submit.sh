#!/usr/bin/env bash
# JIVO harness — UserPromptSubmit hook.
#
# Logs the shape of each question (not to spy on people — to notice when the
# same shape recurs often enough to deserve its own skill). The full question
# text is stored ONLY on this machine (harness/questions/log.jsonl is
# gitignored and never pushed); see harness/README.md
# for what is captured and how to turn it off.
#
# Emits nothing to stdout, so it adds zero tokens to the turn.

set -u
HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[ "${JIVO_HARNESS_NO_LOG:-}" = "1" ] && exit 0
# Accounts runs Windows, where the interpreter is `python` (and `python3`
# is a Store stub that exits non-zero). Try each before giving up.
PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -z "$PY" ] && exit 0

"$PY" "$HARNESS_DIR/bin/harness.py" ask >/dev/null 2>&1 || true
exit 0
