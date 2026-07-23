---
title: Disable the Missing OMS Invoice History Endpoint
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, oms, cli, printing-press, invoices, api-drift]
---

# Patch 0003 — keep `invoices history` disabled until the backend route exists

- **Why:** the deployed OMS backend has no `/api/invoice/history/{id}/` route. The 2026-07-19 verification resolved the path to HTTP 404 and found only the invoice `log/create`, `all`, and `refLogs` routes. Registering the generated command presents a permanently broken read.
- **Live wiring:** `internal/cli/invoices.go` comments out `newInvoicesHistoryCmd(flags)` with the live-verification reason. `oms-spec.yaml` retains the endpoint as a documented backend/SPA mismatch and marks it unregistered.
- **Files:** `internal/cli/invoices.go`, `oms-spec.yaml`; `internal/cli/invoices_history.go` is retained generated residue and must remain unreachable.
- **Re-apply after regeneration:** do not register `newInvoicesHistoryCmd(flags)` unless the backend team confirms the route and a read-only live probe succeeds. If the route ships, update the spec note and this ledger before enabling it.
- **Verification:** `oms-pp-cli invoices --help` must omit `history`; no network probe is needed unless upstream reports that the route has shipped.

Linked: [[CLI/oms-cli/.printing-press-patches/README|OMS patch ledger]] · [[CLI/oms-cli/README|OMS CLI]] · [[docs/oms/OMS_VERIFICATION|OMS_VERIFICATION]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
