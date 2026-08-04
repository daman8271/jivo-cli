---
title: Preserve the OMS MCP GET-Only Guards
created: 2026-08-04
updated: 2026-08-04
project: jivogpt
type: patch
tags: [jivogpt, oms, cli, printing-press, mcp, read-only, security]
---

# Patch 0005 — fail-closed MCP execution in BOTH paths

- **Date:** 2026-08-04 (added during the v0.2.0 rescrape)
- **Why:** the spec is GET-only, but a generated MCP server ships the full
  generic write machinery. The v0.1.0 tree already carried it — **10** mutating
  client calls in `internal/mcp/tools.go` and **8** in `internal/mcp/code_orch.go`
  — with no guard at all, and a fresh `cli-printing-press generate` restores
  them every time.
- **Was it exploitable?** No, and that is exactly why it needs a structural
  guard rather than a shrug. Both paths take the method from the generated
  endpoint catalog (`ep.Method` / `method`), and every catalogued OMS endpoint
  is a GET, so no tool call could select a write branch. The only thing standing
  between the restored machinery and a live write was one future spec edit that
  nobody reviews as a security change. OMS carries
  `POST /api/service-layer/invoice/`, which submits a document into SAP
  Business One.
- **Two paths, and both matter:**
  - `internal/mcp/tools.go` — the direct endpoint-tool handler.
  - `internal/mcp/code_orch.go` — the code-orchestration executor (the
    Cloudflare pattern the press applies above 50 endpoints; this CLI has 108).
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

  **Calibrated in both directions.** Run against the un-patched v0.1.0 tree the
  test failed, naming all 18 offending calls across the two files; run against
  the patched tree it passes. A guard test that has never been seen to fail has
  not been tested.
- **Also enforced by** `research/verify-invariants.sh`, which checks both the
  guard comment and the absence of mutating client calls in each file.

Linked: [[CLI/oms-cli/.printing-press-patches/README|OMS patch ledger]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
