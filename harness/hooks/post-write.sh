#!/usr/bin/env bash
# JIVO harness — PostToolUse hook for Write/Edit.
#
# Stamps the JIVO mark onto any HTML report or Excel workbook the agent just
# wrote, so no report leaves this toolkit without saying who produced it.
#
# This is a hook and not a CLAUDE.md rule on purpose: an instruction is a
# request the model can forget and an operator can talk it out of, a hook runs
# on every write with no model in the loop.
#
# Fails silently and exits 0 always: a broken watermark must never stop someone
# from doing their job. The Python side prints its own diagnostics to stderr,
# which Claude Code surfaces.

set -u
HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# On Windows `python3` is often a Microsoft Store stub: it EXISTS on PATH, so
# `command -v` finds it, but running it prints "Python was not found" and exits
# 9009. Probe by EXECUTING a no-op, not by testing for presence — the weaker
# check picks the stub and silently disables the watermark on every Windows
# laptop, which is the exact failure this hook exists to prevent.
PY=""
for c in python python3 py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "pass" >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
[ -z "$PY" ] && exit 0

"$PY" "$HARNESS_DIR/bin/watermark.py" hook || true
exit 0
