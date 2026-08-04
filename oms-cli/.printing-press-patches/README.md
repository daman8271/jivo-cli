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
| [[CLI/oms-cli/.printing-press-patches/0004-preserve-hana-required-params|0004 — preserve HANA required params]] | Preserve the required `card_code` and `item_code` request contracts — and, from v0.2.0, the required `branch` on all 19 HANA endpoints. | `oms-spec.yaml`; the HANA command files; [[OMS_VERIFICATION]] |
| [[CLI/oms-cli/.printing-press-patches/0005-preserve-mcp-get-only-guards|0005 — preserve MCP GET-only guards]] | Fail-closed refusal of every non-GET method in **both** MCP execution paths. | `internal/mcp/tools.go`; `internal/mcp/code_orch.go`; `internal/mcp/readonly_guard_test.go` |

## Reprint Checklist

0. Run `python3 research/scripts/apply_patches.py` from the CLI root — it applies
   0001, 0002, 0003 and 0005 and FAILS LOUDLY on a missing anchor rather than
   skipping. Then `RESCRAPE_CLI=./oms-pp-cli bash research/verify-invariants.sh`.
1. Re-apply every active patch whose upstream condition still holds.
2. Confirm `auth --help` includes `login`.
3. Confirm top-level help omits `import` and `invoices --help` omits `history`.
4. Confirm `hana so --help` includes `--card-code` and `hana product-so --help` includes `--item-code`.
5. Run `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...`.

## Verification Record — 2026-08-04 (v0.2.0 rescrape)

- 73 -> 108 endpoints. Zero commands dropped, zero renamed (regression gate).
- `gofmt`, `go build ./...`, `go vet ./...`, `go test ./...` all green.
- Invariant gate GREEN, including the new `branch` contract check.
- All 19 `/api/hana/` endpoints now declare a required `branch` param. In
  v0.1.0 none of them did, so all 14 shipped HANA commands returned HTTP 400
  and could never succeed — verified by running the shipped binary, not by
  reading the spec.
- Patch 0005 added; its guard test was calibrated in both directions.
- `govulncheck`: 0 vulnerabilities (needed `toolchain go1.26.5` and
  `golang.org/x/text v0.39.0`).
- One live run per resource group plus three parameterised endpoints.
- **Generation note:** do NOT pass `--spec-source sniffed`. It selects the
  `enetx/surf` browser-impersonation transport, whose headers make DRF
  content-negotiate to its browsable HTML renderer, so every command returns an
  HTML page instead of JSON. Generate with `--transport standard`.

## Verification Record — 2026-07-19

- `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...` passed.
- Runtime help includes native `auth login`, omits generic `import`, omits disabled `invoices history`, and exposes both required HANA flags.
- `tools-manifest.json` contains GET methods only.

There is no `.printing-press.json` or repository history in this workspace, so this ledger records source-level evidence and durable re-apply intent rather than claiming an unavailable base run ID.

Linked: [[CLI/oms-cli/README|OMS CLI]] · [[docs/oms/OMS_MAP|OMS_MAP]] · [[docs/oms/OMS_VERIFICATION|OMS_VERIFICATION]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
