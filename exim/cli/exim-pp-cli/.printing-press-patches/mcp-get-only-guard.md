---
title: Preserve the EXIM MCP GET-Only Guards
created: 2026-08-10
updated: 2026-08-10
project: jivogpt
type: patch
tags: [jivogpt, exim, cli, printing-press, mcp, read-only, security]
---

# Patch — fail-closed MCP execution in BOTH paths

- **Date:** 2026-08-10 (added when EXIM was wired into the unified MCP gateway).
- **Why:** the spec is GET-only and the transport already refuses non-GET
  (see [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/client-readonly-guard|client-readonly-guard]]),
  but the *generated MCP server* still shipped the full generic write machinery:
  `POST`/`PUT`/`PATCH`/`DELETE` branches wired straight to the HTTP client in
  **both** execution paths. Nothing could reach them today — every catalogued
  endpoint is a GET and the client would refuse anyway — but that made the
  transport guard the single load-bearing layer. One regeneration of
  `internal/client/client.go` without patch `client-readonly-guard` re-applied
  would have opened a write path through an agent-trusted surface with no
  operator in the loop.
- **Two paths, and both matter:**
  - `internal/mcp/tools.go` — the direct endpoint-tool handler.
  - `internal/mcp/code_orch.go` — the code-orchestration executor (the
    Cloudflare pattern the press applies above 50 endpoints; this CLI has 65).
    It reaches the same client. **Guarding only `tools.go` leaves this one as a
    complete write bypass.**
- **Change:** in each file the write-method `case` branches were deleted and
  replaced with a `default:` that returns
  `read-only CLI: method %q is not permitted (GET only, per the JivoGPT
  READ-ONLY LAW)` before any client call. The now-dead `writeBody` closure in
  `code_orch.go` was removed; the package-level `codeOrchWriteBody` /
  `codeOrchArrayBody` helpers are deliberately retained because the generated
  write-body unit test exercises them directly, so the body-marshaling contract
  stays pinned even though no live path can reach it.
- **Also in this patch:** `exim_search` and `exim_execute` gained
  `readOnlyHint=true` / `destructiveHint=false`. Both were advertising
  themselves as possibly-destructive despite `exim_search` being a pure local
  catalog lookup and `exim_execute` being GET-only by construction. Hosts
  default to "could write or delete" without the hints, which trains operators
  to click through permission prompts on a read-only surface.
- **RE-APPLY AFTER EVERY REGEN.**
- **Verification — by test, not by reading.** `internal/mcp/readonly_guard_test.go`:
  - `TestNoWriteToolIsRegistered` registers the real tool set through
    `RegisterTools` and fails if any advertised tool name carries a mutating
    verb. This is the behavioural guard: it catches a newly generated command
    reaching the cobratree walker, not just a hand-added typed tool.
  - `TestRegisteredToolSetIsPinned` pins the exact 11-tool surface so a new
    tool must be looked at by a human rather than shipped by a regeneration.
  - `TestMCPExecutionPathsMakeNoWriteClientCall` walks the AST of both files and
    asserts no `c.Post*` / `c.Put*` / `c.Patch*` / `c.Delete*` call exists. This
    is the load-bearing assertion: it does not depend on the current spec being
    GET-only.
  - `TestMCPGuardsRefuseNonGETByConstruction` asserts each path carries the
    fail-closed default branch.
  - `TestCodeOrchCatalogIsGETOnly` asserts every entry in the in-binary
    `codeOrchEndpoints` catalog (what `exim_execute` dispatches against) is a GET.
  - `TestSpecIsGETOnly` is the weaker spec-level check, kept because a failure
    there means `cli/exim-openapi.json` itself grew a write and needs a human
    decision.

  **The tests were calibrated in both directions**: re-adding a single
  `c.PostWithParams(...)` to `tools.go` makes
  `TestMCPExecutionPathsMakeNoWriteClientCall` fail with the offending call
  named, and registering `newImportCmd` in `internal/cli/root.go` makes
  `TestNoWriteToolIsRegistered` fail naming the `import` tool. Both were then
  reverted and the suite passes again. A guard test that has never been seen to
  fail has not been tested.

Linked: [[CLI/exim/cli/exim-pp-cli/.printing-press-patches/README|EXIM patch ledger]] · [[CLI/exim/HARD-RULE|HARD-RULE]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
