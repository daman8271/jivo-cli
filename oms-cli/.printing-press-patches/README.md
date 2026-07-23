---
title: OMS Printed CLI Local Patch Ledger
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: index
tags: [jivogpt, oms, cli, printing-press, patches]
---

# OMS Printed CLI Local Patch Ledger

This directory is the reprint guard for intentional deviations from the generated `oms-pp-cli` tree. A fresh Printing Press run can replace generated files, registrations, and spec-derived parameters; review every entry below after a reprint and keep the runtime read-only.

## Active Patches

| Patch | Contract | Primary evidence |
|---|---|---|
| [[CLI/oms-cli/.printing-press-patches/0001-preserve-native-login|0001 — preserve native login]] | Keep the hand-authored `auth login` session-token exchange and its registration. | `internal/cli/oms_login.go`; `internal/cli/auth.go` |
| [[CLI/oms-cli/.printing-press-patches/0002-remove-generic-import|0002 — remove generic import]] | Keep the generated POST-based `import` command unreachable. | `internal/cli/import.go`; `internal/cli/root.go`; [[READ_ONLY_LAW]] |
| [[CLI/oms-cli/.printing-press-patches/0003-disable-missing-invoice-history|0003 — disable missing invoice history]] | Do not register the backend route that live verification proved absent. | `internal/cli/invoices.go`; `oms-spec.yaml`; [[OMS_VERIFICATION]] |
| [[CLI/oms-cli/.printing-press-patches/0004-preserve-hana-required-params|0004 — preserve HANA required params]] | Preserve the required `card_code` and `item_code` request contracts. | `oms-spec.yaml`; the two HANA command files; [[OMS_VERIFICATION]] |

## Reprint Checklist

1. Re-apply every active patch whose upstream condition still holds.
2. Confirm `auth --help` includes `login`.
3. Confirm top-level help omits `import` and `invoices --help` omits `history`.
4. Confirm `hana so --help` includes `--card-code` and `hana product-so --help` includes `--item-code`.
5. Run `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...`.

## Verification Record — 2026-07-19

- `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...` passed.
- Runtime help includes native `auth login`, omits generic `import`, omits disabled `invoices history`, and exposes both required HANA flags.
- `tools-manifest.json` contains GET methods only.

There is no `.printing-press.json` or repository history in this workspace, so this ledger records source-level evidence and durable re-apply intent rather than claiming an unavailable base run ID.

Linked: [[CLI/oms-cli/README|OMS CLI]] · [[docs/oms/OMS_MAP|OMS_MAP]] · [[docs/oms/OMS_VERIFICATION|OMS_VERIFICATION]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
