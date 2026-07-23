---
title: Keep the Jivo Factory Generic Import Command Absent
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, read-only, provenance]
---

# Patch 0004 — preserve the no-import command surface

- **Invariant:** the current Factory tree contains neither `internal/cli/import.go` nor a `newImportCmd` registration. Top-level help therefore exposes no generic import path.
- **Why it matters:** Printing Press trees can include a generic `import <resource>` scaffold that POSTs records. Any such command would violate [[READ_ONLY_LAW]] for a JIVO source system.
- **Provenance limit:** this workspace has no Git history and no `.printing-press.json`, so source evidence cannot prove whether Factory's import code was deliberately removed after printing or was never emitted by this particular generator run. This entry records the required invariant without claiming an unprovable historical edit.
- **Re-apply after regeneration:** if a future print introduces `import.go` or registers `newImportCmd(flags)`, remove the registration before use. Prefer removing the generated file as well so static scans cannot mistake it for a supported path.
- **Verification:** top-level `--help` must omit `import`; a source scan must find no `newImportCmd` registration.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/README|Jivo Factory CLI]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]]
