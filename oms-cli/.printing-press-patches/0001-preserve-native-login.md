---
title: Preserve the OMS Native Login Command
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, oms, cli, printing-press, authentication]
---

# Patch 0001 — preserve the hand-authored `auth login` command

- **Why:** `internal/cli/oms_login.go` is explicitly hand-authored. It exchanges a username and password at `POST /api/auth/login/`, stores only the returned JWT pair, hides the action from MCP, refuses insecure non-local HTTP origins, and never mutates business data. The generated auth scaffold otherwise exposes only setup/status/token-management commands.
- **Live wiring:** `internal/cli/auth.go` registers `newAuthOmsLoginCmd(flags)` and labels the line hand-authored.
- **Files:** `internal/cli/oms_login.go`, `internal/cli/auth.go`.
- **Re-apply after regeneration:** restore `oms_login.go` if a clean print drops it, then restore the `newAuthOmsLoginCmd(flags)` registration in `newAuthCmd`. Keep `mcp:hidden: true`, HTTPS enforcement, password non-persistence, and verify/dry-run short-circuiting.
- **Read-only boundary:** login creates a session token only. It is the sole permitted OMS authentication POST and must never be generalized into a business-data write path.
- **Verification:** `oms-pp-cli auth --help` must list `login`; normal Go formatting, tests, vet, and build must remain green. No live login is required for the reprint check.

Linked: [[CLI/oms-cli/.printing-press-patches/README|OMS patch ledger]] · [[CLI/oms-cli/README|OMS CLI]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[docs/oms/OMS_MAP|OMS_MAP]]
