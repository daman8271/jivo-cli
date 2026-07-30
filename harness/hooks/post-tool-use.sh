#!/usr/bin/env bash
# JIVO harness — PostToolUse hook (query-pattern capture).
#
# The second learning signal. `user-prompt-submit.sh` records what an operator
# TYPED; this records what actually GOT RUN. Three people asking for a ledger
# balance three different ways produce three question shapes and one query
# shape — and the query shape is the one a skill can be written from.
#
# Captures Bash invocations of the JIVO CLIs and the equivalent mcp__sapb1__* /
# mcp__postsql__* tool calls, normalises them to a reusable skeleton, and
# appends one line to harness/questions/queries.jsonl. It reads only the
# command; the tool's OUTPUT is never touched, so no SAP row and no credential
# can reach the log. See harness/PATTERNS.md for the full guarantee.
#
# This hook fires after EVERY tool call, so it must cost nothing. The regex
# below is a pure-bash pre-filter: for a Read, an Edit or a Grep it exits
# before python3 is ever started, which is the 95% case. Emits nothing on
# stdout (zero tokens added to the turn) and always exits 0.

set -u
HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Honour the documented global switch, plus a pattern-only opt-out.
[ "${JIVO_HARNESS_NO_LOG:-}" = "1" ] && exit 0
[ "${JIVO_PATTERNS_NO_LOG:-}" = "1" ] && exit 0

# No stdin means this was run by hand, not by Claude Code. Nothing to do.
[ -t 0 ] && exit 0

# Bounded read. `payload="$(cat)"` blocks forever on a pipe that is open but
# never delivers EOF, which outlives the hook's own timeout in settings.json and
# stalls the turn. `read -d ''` consumes everything up to EOF and gives up after
# JIVO_PATTERNS_READ_WAIT seconds, so the worst case is bounded and well under
# the 5s hook timeout. It returns non-zero on both EOF and timeout, so the exit
# status is deliberately ignored — $payload holds whatever arrived either way.
payload=""
IFS= read -r -d '' -t "${JIVO_PATTERNS_READ_WAIT:-3}" payload 2>/dev/null || true
[ -z "$payload" ] && exit 0

# Pure-bash pre-filter — no fork, no interpreter start. A false positive just
# means python runs and correctly rejects the payload, so this can stay loose.
if [[ ! "$payload" =~ (sapb1|postsql|hana-sql|hanasql|dsr|ecom|oms|factory|exim) ]]; then
  exit 0
fi

# Accounts runs Windows, where the interpreter is `python` (and `python3`
# is a Store stub that exits non-zero). Try each before giving up.
PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -z "$PY" ] && exit 0

printf '%s' "$payload" \
  | "$PY" "$HARNESS_DIR/bin/patterns.py" record >/dev/null 2>&1 || true
exit 0
