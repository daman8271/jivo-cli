#!/usr/bin/env python3
"""A stand-in for the real `sapb1` binary, for tests.

It contacts nothing. It records how it was called and replies with whatever the
test told it to reply, so `SapCli` can be exercised against every exit code the
Go CLI can produce without a network, a login, or a live SAP.

Driven entirely by environment variables:

  STUB_LOG       file to append one JSON line per call: {"argv": [...], "cwd": "...",
                 "env": {SAPB1_* only}}
  STUB_EXIT      exit code to return (default 0)
  STUB_EXIT_SEQ  comma-separated exit codes, one consumed per call, last one
                 repeating — for retry/backoff tests. Overrides STUB_EXIT.
  STUB_STDOUT    exact text to print on stdout (default "[]")
  STUB_REPLIES   path to a JSON list of {"when": "<substring of the joined argv>",
                 "stdout": "...", "exit": 0}. First match wins; no match falls
                 through to STUB_STDOUT. This is how one run can answer several
                 different questions — a batch asks about a GRPO, a vendor, the
                 drafts, and then sends one.
  STUB_STDERR    exact text to print on stderr
  STUB_SIGNAL    kill this process with that signal number instead of exiting —
                 the only way to produce a NEGATIVE returncode, which is what a
                 sapb1 killed mid-write actually looks like from Python
  STUB_SLEEP     seconds to sleep before answering, for the subprocess-timeout tests
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path


def main() -> int:
    log = os.environ.get("STUB_LOG")
    call_no = 0
    if log:
        path = Path(log)
        try:
            call_no = sum(1 for _ in path.open(encoding="utf-8"))
        except FileNotFoundError:
            call_no = 0
        record = {
            "argv": sys.argv[1:],
            "cwd": os.getcwd(),
            "env": {k: v for k, v in os.environ.items() if k.startswith("SAPB1_")},
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    if os.environ.get("STUB_SLEEP"):
        time.sleep(float(os.environ["STUB_SLEEP"]))
    if os.environ.get("STUB_SIGNAL"):
        os.kill(os.getpid(), int(os.environ["STUB_SIGNAL"]))
        time.sleep(5)                       # unreachable in practice

    seq = os.environ.get("STUB_EXIT_SEQ")
    if seq:
        codes = [int(c) for c in seq.split(",") if c.strip()]
        code = codes[min(call_no, len(codes) - 1)]
    else:
        code = int(os.environ.get("STUB_EXIT", "0"))

    out = os.environ.get("STUB_STDOUT", "[]")
    replies = os.environ.get("STUB_REPLIES")
    if replies:
        joined = " ".join(sys.argv[1:])
        for rule in json.loads(Path(replies).read_text(encoding="utf-8")):
            if rule.get("when", "") in joined:
                out = rule.get("stdout", out)
                code = int(rule.get("exit", code))
                break

    sys.stdout.write(out)
    sys.stderr.write(os.environ.get("STUB_STDERR", ""))
    return code


if __name__ == "__main__":
    sys.exit(main())
