---
title: EXIM CLI generic import command disabled
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags:
  - exim
  - cli
  - printing-press
  - read-only
---

# EXIM CLI generic import command disabled

## Intent

Printing Press generates a generic `import <resource>` command that submits
arbitrary JSONL records through POST create or upsert requests. That capability
contradicts [[HARD-RULE]] and [[READ_ONLY_LAW]], so EXIM deliberately leaves the
generated implementation unregistered and unreachable from the root command
tree.

The generated `internal/cli/import.go` file remains in place. Keeping the
generated file minimizes reprint drift; command-tree registration is the
security boundary, backed by the absolute client transport guard.

## Customized files

- `internal/cli/root.go` — omits `newImportCmd(flags)` from root registration.
- `internal/cli/root_test.go` — proves `import` is absent and an attempted
  invocation returns Cobra's unknown-command error.

## Reapply after a print

After every clean reprint or `generate --force`:

1. Remove `rootCmd.AddCommand(newImportCmd(flags))` from `newRootCmd`.
2. Restore `TestRootCommandOmitsGenericImport` if the generated test tree
   overwrote it.
3. Rebuild the binary and confirm `./exim-pp-cli --help` contains no `import`
   command.
4. Confirm `./exim-pp-cli import stock-status --input records.jsonl` exits
   non-zero with `unknown command "import"` before running `go test ./...`,
   `go vet ./...`, and `go build ./...`.

Linked: [[HARD-RULE]] · [[READ_ONLY_LAW]]
