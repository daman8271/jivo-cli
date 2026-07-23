---
title: EXIM CLI native authentication login
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags:
  - exim
  - cli
  - printing-press
  - authentication
---

# EXIM CLI native authentication login

## Intent

`internal/cli/exim_login.go` adds `exim-pp-cli auth login`, exchanging an email
and password for JWT credentials and persisting them through
`config.SaveTokens`. This zero-business-data authentication exchange is the
only permitted non-GET operation under [[HARD-RULE]] and [[READ_ONLY_LAW]].

The login implementation intentionally uses its own `http.Client`, keeping it
separate from the generated API client whose transport rejects every non-GET
business request.

## Customized files

- `internal/cli/exim_login.go` — implements the native login exchange.
- `internal/cli/auth.go` — registers `newAuthLoginCmd(flags)` beneath `auth`.

## Reapply after a print

After every clean reprint:

1. Restore `internal/cli/exim_login.go`.
2. Add `cmd.AddCommand(newAuthLoginCmd(flags))` in
   `internal/cli/auth.go`.
3. Run `gofmt` on both files, followed by `go test ./...`, `go vet ./...`, and
   `go build ./...`.

A warm `generate --force` normally preserves the implementation file but may
drop command registration, so always inspect the `auth` command tree after a
reprint.

Linked: [[HARD-RULE]] · [[READ_ONLY_LAW]]
