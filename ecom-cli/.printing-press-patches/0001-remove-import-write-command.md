---
title: Remove the Ecom Import Write Command
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, ecom, cli, printing-press, read-only]
---

# Patch 0001 — remove the `import` write command (JivoGPT RULE 0)

- **Date:** 2026-07-19
- **Why:** JivoGPT's READ_ONLY_LAW (RULE 0) forbids any write to a JIVO source
  system. The printing-press scaffold ships a generic `import <resource>` command
  (`internal/cli/import.go`) whose `RunE` calls `c.Post(ctx, "/"+resource, body)` —
  a live, unguarded POST to `ecom.jivo.in`. The credential in use is a Super-Admin
  JWT (145 permissions incl. `add_*`), so this path *could* actually mutate source data.
  It is the ONLY write path to the source system in this CLI (the `api` command is a
  read-only endpoint browser; `feedback` POSTs only to a user-configured URL; `sync`
  reads).
- **Change:** removed `rootCmd.AddCommand(newImportCmd(flags))` from
  `internal/cli/root.go`. The command is no longer registered, discoverable, or runnable
  (`import` → `unknown command`). `newImportCmd` remains defined but unreferenced.
- **RE-APPLY AFTER EVERY REGEN:** `cli-printing-press generate --force` regenerates
  `root.go` and re-adds the registration. After any regenerate, delete the
  `rootCmd.AddCommand(newImportCmd(flags))` line again. Ideally also request a
  read-scoped token from the ecom.jivo.in owner so writes are impossible, not merely
  disallowed (defense in depth).
- **Verified:** `go build` green; `--help` shows no `import`; `import x` → `unknown command`.

Linked: [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
