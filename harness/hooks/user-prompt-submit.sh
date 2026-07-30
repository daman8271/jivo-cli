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

"$PY" "$HARNESS_DIR/bin/harness.py" ask >/dev/null 2>&1 || true
exit 0
