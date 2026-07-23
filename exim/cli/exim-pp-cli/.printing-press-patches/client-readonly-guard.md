---
title: EXIM CLI transport read-only guard
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

# EXIM CLI transport read-only guard

## Intent

The generated HTTP client is locally hardened to reject every non-GET request
before URL construction, authentication, dry-run handling, verify-mode
short-circuiting, or network transport. This is the executable backstop for
[[HARD-RULE]] and [[READ_ONLY_LAW]].

The sole permitted POST is the zero-business-data authentication exchange in
`internal/cli/exim_login.go`. It intentionally uses its own `http.Client` and
does not pass through the generated API client.

## Customized files

- `internal/client/client.go` — `doInternal` returns the EXIM read-only refusal
  for every method other than GET.
- `internal/client/client_verify_short_circuit_test.go` — generated
  verify-mode assumptions are replaced with tests proving that normal mode,
  verify mode, verify-live mode, and `doRead` cannot bypass the refusal.

## Reapply after a print

After every clean reprint or `generate --force`:

1. Restore the method check at the very start of `doInternal`, before the
   generated verify-mode gate:

   ```go
   if method != http.MethodGet {
       return nil, 0, fmt.Errorf("read-only CLI: refusing %s %s (only GET is permitted against EXIM)", method, path)
   }
   ```

2. Restore the local client tests so non-GET calls through both `do` and
   `doRead` expect the exact refusal, nil body, zero status, and zero transport
   calls under no-env, verify, and verify-live configurations.
3. Keep the GET control test proving that the guard does not block permitted
   reads.
4. Run `gofmt -w internal/client/client_verify_short_circuit_test.go`,
   `go test ./...`, `go vet ./...`, and `go build ./...`.

Linked: [[HARD-RULE]] · [[READ_ONLY_LAW]]
