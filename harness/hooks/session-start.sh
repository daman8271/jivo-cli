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
"$PY" "$HARNESS_DIR/bin/harness.py" context 2>/dev/null || true

# Integrity check. `-q` stays silent when everything matches, so this costs
# nothing on a normal session; when a protected file HAS changed it prints to
# stderr, which lands in the agent's context at session start — the earliest
# possible moment somebody can be told the rules were edited.
# Guard is optional: it may not be present on a clone that predates it.
# Without this test the hook prints a Python "no such file" error into
# every operator's session at startup.
[ -f "$HARNESS_DIR/bin/guard.py" ] && "$PY" "$HARNESS_DIR/bin/guard.py" check -q 2>&1 || true
exit 0
