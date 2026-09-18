"""apbatch — the shared engine behind `acc batch` and the ap-rm-pm skill.

Nothing in here talks to SAP except through `sap.SapCli`, which shells out to
the `sapb1` binary. That is deliberate: every safety property Accounts relies on
(the confirmation prompt, the write log, the exit-7 "went out, no answer back"
distinction) lives in the Go CLI, and re-implementing the Service Layer call in
Python would fork it.

Layout:
  sap.py      the subprocess wrapper + its exit-code -> exception map
  rules.py    pure functions: no I/O, no SAP, fully unit-testable
  context.py  per-run caches over SAP reads
  precheck.py one GRPO -> a decision (status, payload, TDS, series)
  readback.py a draft as SAP holds it -> the gaps in it
  xlsx.py     zero-dependency Excel writer/reader
  store.py    batch ids, sidecars, journals
  batch_scan.py / batch_send.py / batch_status.py   the three subcommands
"""

from __future__ import annotations

__all__ = ["sap", "rules", "context", "precheck", "readback", "xlsx", "store",
           "batch_scan", "batch_send", "batch_status"]
