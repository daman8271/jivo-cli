#!/usr/bin/env bash
# JIVO harness — UserPromptSubmit hook.
#
# Logs the shape of each question (not to spy on people — to notice when the
# same shape recurs often enough to deserve its own skill). The full question
# text is stored ONLY on this machine (harness/questions/log.jsonl is
# gitignored and never pushed); see harness/README.md
# for what is captured and how to turn it off.
#
# Emits nothing to stdout for an ordinary question. When the prompt looks like
# an SAP entry it prints the skill-router nudge (harness/bin/skill_router.py),
# which is what makes the entry skills fire on their own.

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

_in="$(cat 2>/dev/null)"
printf '%s' "$_in" | "$PY" "$HARNESS_DIR/bin/harness.py" ask >/dev/null 2>&1 || true

# Skill router: when the prompt looks like an SAP entry, name the skill to
# invoke first (stdout of this hook is added to the turn's context). It prints
# nothing for an ordinary question, so those still cost zero tokens.
if [ -f "$HARNESS_DIR/bin/skill_router.py" ]; then
  _nudge="$(printf '%s' "$_in" | "$PY" "$HARNESS_DIR/bin/skill_router.py" match 2>/dev/null || true)"
  if [ -n "$_nudge" ]; then
    printf '%s\n' "$_nudge"
    # On a drafts-only desk the entry nudge must never be the last word — the
    # session has just been told to enter a document, and this is the sentence
    # that says where entering STOPS. One line; the full banner is at session
    # start and the binary refuses regardless.
    if [ -f "$HARNESS_DIR/bin/desk.py" ] && "$PY" "$HARNESS_DIR/bin/desk.py" policy 2>/dev/null | head -1 | grep -q "DRAFTS ONLY"; then
      printf '%s\n' "[jivo desk] DRAFTS ONLY desk: build the draft, say its number, STOP. Never \`sapb1 add-draft\`, never post - the operator presses Add herself in SAP B1."
    fi
  fi
fi
exit 0
