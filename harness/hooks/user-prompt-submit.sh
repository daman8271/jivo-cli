#!/usr/bin/env bash
# JIVO harness — UserPromptSubmit hook.
#
# Logs the shape of each question (not to spy on people — to notice when the
# same shape recurs often enough to deserve its own skill). The full question
# text is stored locally in harness/questions/log.jsonl; see harness/README.md
# for what is captured and how to turn it off.
#
# Emits nothing to stdout, so it adds zero tokens to the turn.

set -u
HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[ "${JIVO_HARNESS_NO_LOG:-}" = "1" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0

python3 "$HARNESS_DIR/bin/harness.py" ask >/dev/null 2>&1 || true
exit 0
