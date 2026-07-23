---
title: Preserve the Jivo Factory Native Login Command
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, authentication]
---

# Patch 0001 — preserve the hand-authored `auth login` command

- **Why:** `internal/cli/factory_login.go` is explicitly hand-authored for the Factory API. It exchanges email and password at `POST /accounts/login/`, stores only the returned JWT pair, hides login from MCP, and never mutates business data. It also supports secure local credential sources without persisting the password.
- **Live wiring:** `internal/cli/auth.go` registers `newAuthFactoryLoginCmd(flags)` alongside the generated auth commands.
- **Files:** `internal/cli/factory_login.go`, `internal/cli/auth.go`.
- **Re-apply after regeneration:** restore `factory_login.go` if a clean print drops it, then restore the `newAuthFactoryLoginCmd(flags)` registration. Preserve `mcp:hidden: true`, password non-persistence, HTTPS enforcement, and verify/dry-run short-circuiting.
- **Read-only boundary:** login creates a session token only. It is a permitted authentication exchange, not permission to add any business-data write command.
- **Verification:** `jivo-factory-pp-cli auth --help` must list `login`; normal Go formatting, tests, vet, and build must remain green. No live login is required for the reprint check.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/README|Jivo Factory CLI]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
