---
title: Preserve the Jivo Ecom MCP GET-Only Guards
created: 2026-08-03
updated: 2026-08-03
project: jivogpt
type: patch
tags: [jivogpt, ecom, cli, printing-press, mcp, read-only, security]
---

# Patch 0004 — fail-closed MCP execution in BOTH paths

- **Date:** 2026-08-03 (added during the v0.2.0 rescrape)
- **Why:** the spec is GET-only, but a generated MCP server ships the full
  generic write machinery. The 2026-08-03 regeneration restored
  `POST`/`PUT`/`PATCH`/`DELETE` branches wired straight to the HTTP client in
  **both** execution paths. Nothing in the pipeline objected: the spec is
  GET-only, so no live call could reach them — but a single future spec edit,
  or a hand-added endpoint, would have opened a write path through an
  agent-trusted surface with no operator in the loop.
- **Two paths, and both matter:**
  - `internal/mcp/tools.go` — the direct endpoint-tool handler.
  - `internal/mcp/code_orch.go` — the code-orchestration executor (the
    Cloudflare pattern the press applies above 50 endpoints; this CLI has 151).
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
- **RE-APPLY AFTER EVERY REGEN:** `research/scripts/apply_patches.py` does it,
  and fails loudly if the expected shape is not found rather than skipping.
- **Verification — by test, not by reading.** `internal/mcp/readonly_guard_test.go`:
  - `TestMCPExecutionPathsMakeNoWriteClientCall` walks the AST of both files and
    asserts no `c.Post*` / `c.Put*` / `c.Patch*` / `c.Delete*` call exists. This
    is the load-bearing assertion: it does not depend on the current spec being
    GET-only.
  - `TestMCPGuardsRefuseNonGETByConstruction` asserts each path carries the
    fail-closed default branch.
  - `TestSpecIsGETOnly` is the weaker spec-level check, kept because a failure
    there means the spec itself grew a write and needs a human decision.

  **The test was calibrated in both directions**: re-adding a single
  `c.PostWithParams(...)` to `tools.go` makes it fail with the offending call
  named, and removing it makes it pass again. A guard test that has never been
  seen to fail has not been tested.
- **Also enforced by** `research/verify-invariants.sh`, which checks both the
  guard comment and the absence of mutating client calls in each file.

Linked: [[CLI/ecom-cli/.printing-press-patches/README|Ecom patch ledger]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
