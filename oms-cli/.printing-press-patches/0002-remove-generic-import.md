---
title: Remove the OMS Generic Import Write Command
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, oms, cli, printing-press, read-only]
---

# Patch 0002 — keep the generated `import` write command unregistered

- **Why:** the generated `internal/cli/import.go` defines `import <resource>` and sends a live `POST` through `c.Post`. [[READ_ONLY_LAW]] forbids JivoGPT from writing to JIVO source systems.
- **Live wiring:** `internal/cli/root.go` contains an explicit read-only-law comment where the generated import registration would normally sit, but does not call `rootCmd.AddCommand(newImportCmd(flags))`. The source file remains as generator residue; it is unreachable from the Cobra tree and therefore absent from CLI help and MCP mirroring.
- **Files:** `internal/cli/root.go`; `internal/cli/import.go` is evidence only and should remain unreachable.
- **Re-apply after regeneration:** remove any `newImportCmd(flags)` registration. Deleting the source file is optional; removing the registration is the behaviorally decisive safeguard.
- **Verification:** top-level `--help` must not list `import`, and invoking `import` must return an unknown-command usage error without sending a request.

Linked: [[CLI/oms-cli/.printing-press-patches/README|OMS patch ledger]] · [[CLI/oms-cli/README|OMS CLI]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[docs/oms/OMS_VERIFICATION|OMS_VERIFICATION]]
