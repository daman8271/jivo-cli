---
title: Preserve the Jivo Factory MCP GET-Only Guards
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, mcp, read-only, security]
---

# Patch 0003 — preserve fail-closed MCP execution

- **Why:** the current spec is GET-only, but generated MCP executors contain generic write-method machinery. A later spec edit or regeneration must not silently expose POST, PUT, PATCH, or DELETE through an agent-trusted MCP surface.
- **Direct tool guard:** `internal/mcp/tools.go` dispatches only `GET`; every other method returns a READ_ONLY_LAW error before calling the client.
- **Code-orchestration guard:** `internal/mcp/code_orch.go` dispatches only `GET`; every other endpoint method returns the same fail-closed error before transport execution.
- **Files:** `internal/mcp/tools.go`, `internal/mcp/code_orch.go`, and MCP tests.
- **Re-apply after regeneration:** restore both guards. Protecting only the direct tool path leaves the code-orchestration executor as a write bypass.
- **Verification:** focused tests must inject or construct a non-GET endpoint and prove both handlers return an error without invoking the client. The normal manifest scan must also show every currently published endpoint is GET.

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/README|Jivo Factory CLI]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]]
