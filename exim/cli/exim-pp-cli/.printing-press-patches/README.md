---
title: EXIM Printed CLI Local Patch Ledger
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: index
tags: [jivogpt, exim, cli, printing-press, patches]
---

# EXIM Printed CLI Local Patch Ledger

This directory records the three load-bearing deviations from the generated
`exim-pp-cli` tree. Review and re-apply them after every Printing Press run.

## Active patches

| Patch | Contract |
|---|---|
| [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/auth-login|Native auth login]] | Preserve the authentication-only login exchange and registration. |
| [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/client-readonly-guard|Transport GET-only guard]] | Reject every non-GET method before transport. |
| [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/generic-import-disabled|Generic import disabled]] | Keep the generated POST import command unreachable. |

## Reprint checklist

1. Re-apply all three patches.
2. Confirm `auth --help` includes `login` and top-level help omits `import`.
3. Confirm `cli/exim-openapi.json` contains GET operations only.
4. Run `gofmt`, `go test ./...`, `go vet ./...`, and `go build ./...`.
5. Verify `./exim raw` rejects the entire underscore `/sap_sync/` namespace.

Linked: [[CLI/exim/cli/exim-pp-cli/README|EXIM CLI]] · [[CLI/exim/HARD-RULE|HARD-RULE]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
