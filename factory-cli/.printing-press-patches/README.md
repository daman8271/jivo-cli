---
title: Jivo Factory Printed CLI Local Patch Ledger
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: index
tags: [jivogpt, factory, cli, printing-press, patches]
---

# Jivo Factory Printed CLI Local Patch Ledger

This directory is the reprint guard for intentional deviations from the generated `jivo-factory-pp-cli` tree. A fresh Printing Press run can replace hand-authored files and generated-file edits; review every entry below after a reprint and keep every source-system surface read-only.

## Active Patches

| Patch | Contract | Primary evidence |
|---|---|---|
| [[CLI/factory-cli/.printing-press-patches/0001-preserve-native-login|0001 — preserve native login]] | Keep the hand-authored Factory JWT login and its auth registration. | `internal/cli/factory_login.go`; `internal/cli/auth.go` |
| [[CLI/factory-cli/.printing-press-patches/0002-preserve-multi-company-scope|0002 — preserve multi-company scope]] | Preserve the company flag/env normalization, request header, and cache partition. | `internal/client/company.go`; `internal/cli/root.go`; `internal/client/client.go` |
| [[CLI/factory-cli/.printing-press-patches/0003-preserve-mcp-get-only-guards|0003 — preserve MCP GET-only guards]] | Fail closed on every non-GET endpoint in both MCP execution paths. | `internal/mcp/tools.go`; `internal/mcp/code_orch.go` |
| [[CLI/factory-cli/.printing-press-patches/0004-keep-generic-import-absent|0004 — keep generic import absent]] | Preserve the current no-import command surface; historical removal is unproven. | source-tree and root-command absence; [[READ_ONLY_LAW]] |
| [[CLI/factory-cli/.printing-press-patches/0005-preserve-oil-release-pagination|0005 — scope Oil release to JIVO_OIL]] | Keep the pagination flags, and scope the command to the Oil company — the HANA view exists only in `JIVO_OIL_HANADB`. **Revised 2026-08-03: the 503 is company scope, not missing pagination.** | `internal/cli/barcode_production-release-oil.go` |
| [[CLI/factory-cli/.printing-press-patches/0006-preserve-product-identity-consumer|0006 — preserve product identity consumer]] | Keep one fail-closed, read-only consumer of the shared qualified listing/JID/Factory identity contract. | `internal/cli/product_identity.go`; `internal/cli/product_identity_test.go`; `internal/cli/root.go`; `internal/cli/which.go`; `README.md`; rebuilt CLI/MCP binaries |
| [[CLI/factory-cli/.printing-press-patches/0007-exclude-get-with-side-effects|0007 — exclude GETs that mutate]] | A GET-only surface is not a read-only surface. Never publish `/marketplace/settings/` — reading it creates rows. Clear every key-lookup endpoint before publishing. | `spec.yaml`; `tools-manifest.json`; marketplace command files; correction C-0007 |
| [[CLI/factory-cli/.printing-press-patches/0008-pin-go-toolchain-1-26-5|0008 — pin Go toolchain >= 1.26.5]] | GO-2026-5856 (crypto/tls ECH privacy leak) is reachable from the MCP server's TLS transport. `go.mod` must say `toolchain go1.26.5` or newer. | `go.mod`; `research/verify-invariants.sh` |

## Reprint Checklist

1. Re-apply every active patch whose upstream condition still holds.
2. Confirm `auth --help` includes `login` and top-level help includes `--company`.
3. Confirm top-level help omits `import`.
4. Confirm both MCP dispatch paths reject non-GET methods even if a future spec introduces one.
5. Confirm `barcode production-release-oil --help` includes `--page`, `--page-size` and the `--company oil` requirement.
6. Confirm top-level help includes `product`; prove a bare Factory item code fails without explicit company and returns qualified collisions with `--all-companies`.
7. Confirm `/marketplace/settings/` appears in neither the command tree nor `tools-manifest.json`, and that no published endpoint is on the suspected-`get_or_create` list (patch 0007).
8. Confirm `grep '^toolchain ' go.mod` reads 1.26.5 or newer, and that `govulncheck ./...` reports 0 affected vulnerabilities.
9. Run `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...`.

## Verification Record — 2026-07-19

- `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...` passed.
- Runtime help includes native `auth login` and `--company`, omits generic `import`, and exposes both Oil-release pagination flags.
- `tools-manifest.json` contains GET methods only; source assertions confirm both MCP execution paths fail closed on non-GET methods.
- A dry run of `barcode production-release-oil --company oil` emitted `page=1` and `page_size=100` and explicitly sent no request.

There is no `.printing-press.json` or repository history in this workspace, so this ledger records source-level evidence and durable re-apply intent rather than claiming an unavailable base run ID.

Linked: [[CLI/factory-cli/README|Jivo Factory CLI]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
