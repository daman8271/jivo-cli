#!/usr/bin/env bash
# JIVO harness — skill trigger dispatcher (UserPromptSubmit).
#
# A skill's `description` is only a hint the model may or may not act on. Each
# skill may ship `hooks/trigger.sh`, which reads the operator's prompt and, on a
# match, prints a <system-reminder> naming the skill to invoke. Claude Code
# injects a UserPromptSubmit hook's stdout into the turn, so the instruction
# arrives BEFORE any tool call is chosen.
#
# Those per-skill hooks existed but nothing ever called them — settings.json
# registers only the harness hooks, so every skill trigger on every box was dead
# code. This dispatcher is the missing caller: it runs all of them.
#
# Design rules (same as the hooks it calls):
#   - fail open, always exit 0. A hook must never block an operator.
#   - stdin can only be consumed once, so read it here and feed each trigger a
#     copy. A trigger that reads nothing would silently never match.
#   - print nothing on a non-match, so ordinary turns cost zero extra tokens.
#   - no interpreter dependency — Accounts runs Windows where `python3` is a
#     Store stub. Pure shell and grep.
#
# Turn it off for one session with:  export JIVO_NO_SKILL_TRIGGERS=1

set -u
[ "${JIVO_NO_SKILL_TRIGGERS:-}" = "1" ] && exit 0

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || exit 0
SKILLS="$REPO/.claude/skills"
[ -d "$SKILLS" ] || exit 0

# Read the whole UserPromptSubmit JSON object once, with a timeout so a hook can
# never hang the session waiting on stdin.
INPUT=""
if ! IFS= read -r -d '' -t 2 INPUT 2>/dev/null; then
  : # a partial or timed-out read is fine — whatever arrived is in INPUT
fi
[ -z "$INPUT" ] && exit 0

for trigger in "$SKILLS"/*/hooks/trigger.sh; do
  [ -f "$trigger" ] || continue
  # Each trigger gets its own copy of stdin and its own 5s ceiling. One slow or
  # broken trigger must not starve the rest, and none of them may fail the turn.
  printf '%s\0' "$INPUT" | bash "$trigger" 2>/dev/null || true
done

exit 0
