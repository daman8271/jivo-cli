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

## Reprint checklist

1. Re-apply every active patch whose upstream condition still holds.
2. Confirm top-level help omits `import`.
3. Confirm `auth --help` includes `login` and top-level help includes `api`.
4. Confirm `tools-manifest.json` contains 138 GET tools and no write method.
5. Run `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...`.

Linked: [[CLI/ecom-cli/README|Ecom CLI]] · [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
