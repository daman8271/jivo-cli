---
title: Jivo Ecom Printed CLI Local Patch Ledger
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: index
tags: [jivogpt, ecom, cli, printing-press, patches]
---

# Jivo Ecom Printed CLI Local Patch Ledger

This directory is the reprint guard for intentional deviations from the generated
`jivo-ecom-pp-cli` tree. A fresh Printing Press run can replace registrations and
hand-authored files, so review every entry below after a reprint.

## Active patches

| Patch | Contract |
|---|---|
| [[CLI/ecom-cli/.printing-press-patches/0001-remove-import-write-command|0001 — remove generic import]] | Keep the generated POST-based `import` command unreachable. |
| [[CLI/ecom-cli/.printing-press-patches/0002-restore-auth-login|0002 — restore native login]] | Preserve the hand-authored authentication-only `auth login` command and registration. |
| [[CLI/ecom-cli/.printing-press-patches/0003-restore-api-discovery|0003 — restore API discovery]] | Preserve the network-free `api` command and its registration. |
| [[CLI/ecom-cli/.printing-press-patches/0004-preserve-mcp-get-only-guards|0004 — MCP GET-only guards]] | Keep both MCP execution paths fail-closed against every write method. |

## Reprint checklist

Do not do this by hand. `research/scripts/refold.sh <fresh-tree> <spec.yaml>`
runs the whole sequence, and `research/scripts/apply_patches.py` re-applies all
four patches, failing loudly if an anchor is missing rather than skipping.

1. Re-apply every active patch whose upstream condition still holds.
2. Confirm top-level help omits `import`.
3. Confirm `auth --help` includes `login` and top-level help includes `api`.
4. Confirm the spec declares GET only and no write method reaches the MCP.
5. Run `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...`.
6. Run `bash research/scripts/verify-patches.sh` — checks patch behaviour, not
   the presence of a symbol.
7. Run `RESCRAPE_CLI=./jivo-ecom-pp-cli bash research/verify-invariants.sh`.
8. Run at least one command per resource against the live API. The 2026-08
   reprint passed the build, the full test suite and every patch check while
   sending a literal `{}` to the server on all 62 parameterised endpoints —
   only a real run caught it.

Linked: [[CLI/ecom-cli/README|Ecom CLI]] · [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
