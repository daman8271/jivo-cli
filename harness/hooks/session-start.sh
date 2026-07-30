#!/usr/bin/env bash
# JIVO harness — SessionStart hook.
#
# Injects the persona-filtered corrections digest into every session, so a
# correction one operator recorded reaches every other operator's Claude.
#
# NEVER blocks the operator — but it is no longer silent when it breaks.
# Exit 0 is completely invisible in Claude Code; exit 1 is non-blocking but
# surfaces "<hook> hook error" plus the first stderr line in the transcript.
# That distinction cost us three bugs: a hook that was never registered, a
# UnicodeEncodeError that emptied the digest on every Windows machine, and a
# tracked log that aborted every git pull. All three looked exactly like
# success. So: working -> exit 0 and stay quiet; genuinely broken -> exit 1
# with one line saying so, and let the operator's session show it.

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
if [ -z "$PY" ]; then
  echo "jivo-harness: no working python found (tried python3, python, py) — corrections are NOT loaded. Run: python harness/bin/doctor.py" >&2
  exit 1
fi

# Bring in corrections other operators recorded, before building the digest, so
# this session starts with the team's current knowledge rather than yesterday's.
# Accounts staff will not run `git pull`, so this has to be automatic or the
# sharing half of the harness is decoration.
#
# Budget is deliberately tight: the SessionStart hook has a 10s ceiling, and a
# slow VPN must never make Claude feel broken at startup. On timeout we simply
# use the corrections already on disk. `--quiet` keeps a normal "already up to
# date" out of the operator's context; a real problem still prints.
if [ -f "$HARNESS_DIR/bin/sync.py" ] && [ "${JIVO_NO_AUTOSYNC:-}" != "1" ]; then
  JIVO_SYNC_TIMEOUT=6 "$PY" "$HARNESS_DIR/bin/sync.py" pull --quiet 2>&1 || true
fi

# Capture instead of streaming, so a crash can be reported rather than
# silently producing an empty digest.
_ctx="$("$PY" "$HARNESS_DIR/bin/harness.py" context 2>/tmp/jivo-harness-err.$$)"
_rc=$?
if [ $_rc -ne 0 ]; then
  echo "jivo-harness: corrections failed to load (exit $_rc) — you are running WITHOUT the team's corrections. $(head -1 /tmp/jivo-harness-err.$$ 2>/dev/null)" >&2
  rm -f /tmp/jivo-harness-err.$$
  exit 1
fi
rm -f /tmp/jivo-harness-err.$$
printf '%s' "$_ctx"

# Integrity check. `-q` stays silent when everything matches, so this costs
# nothing on a normal session; when a protected file HAS changed it prints to
# stderr, which lands in the agent's context at session start — the earliest
# possible moment somebody can be told the rules were edited.
# Guard is optional: it may not be present on a clone that predates it.
# Without this test the hook prints a Python "no such file" error into
# every operator's session at startup.
[ -f "$HARNESS_DIR/bin/guard.py" ] && "$PY" "$HARNESS_DIR/bin/guard.py" check -q 2>&1 || true
exit 0
