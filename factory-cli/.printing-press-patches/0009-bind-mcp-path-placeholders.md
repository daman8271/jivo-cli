---
title: Bind Path Placeholders in the MCP Code-Orchestration Executor
created: 2026-08-11
updated: 2026-08-11
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, mcp, correctness]
---

# Patch 0009 — the MCP executor never substituted `{id}`

- **Why:** `handleCodeOrchExecute` resolved path placeholders from
  `ep.Positional` only:

  ```go
  path := ep.Path
  for _, p := range ep.Positional {
      if v, ok := params[p]; ok {
          path = strings.ReplaceAll(path, "{"+p+"}", formatMCPParamValue(v))
          delete(params, p)
      }
  }
  ```

  The press emitted `Positional: []string{}` for all but **2** of the
  **110** endpoints whose path carries a placeholder. For the other 108 the loop
  ran zero times, the literal `{id}` survived into the request URL, and the
  Django server answered:

  ```
  GET /production-execution/runs/{id}/  ->  HTTP 404  <!doctype html> ... Not Found
  ```

  `TemplateParams` was declared and documented on the struct for exactly this
  purpose and was **never read anywhere in the package**.

- **Why it went unnoticed:** the CLI path is generated separately and calls
  `replacePathParam`, so `jivo-factory-pp-cli production-execution run-detail
  --id 187` always worked. Only the agent-facing MCP surface was broken, and it
  failed with a 404 whose body reads like *"this endpoint does not exist"* —
  so the natural conclusion was a bad endpoint id, not a broken executor.
  Verified live 2026-08-11: identical failure on `run-detail`,
  `line-clearance-detail` and the newly added `line-config-detail`.

- **Scope:** factory only. `exim-pp-cli` emits non-empty `Positional` for all
  six of its placeholder endpoints and is unaffected. Any CLI whose
  `code_orch.go` shows `Positional: []string{}` alongside a `Path` containing
  `{` has this bug.

- **The fix:** after the `Positional` pass, bind remaining placeholders through
  `TemplateParams` (public→wire), then by name from `params`. Then refuse to
  issue a request that still contains one:

  ```go
  if missing := pathPlaceholderNames(path); len(missing) > 0 {
      return mcplib.NewToolResultError(fmt.Sprintf(
          "endpoint %s needs path parameter(s) %s — pass them in params, ...",
          ep.ID, strings.Join(missing, ", "), missing[0])), nil
  }
  ```

  A missing id now produces an actionable error instead of an HTML 404 that
  sends the caller to debug the wrong layer.

- **Invariant:** every endpoint whose `Path` carries a placeholder must be able
  to bind it from `params`. Pinned by
  `internal/mcp/code_orch_pathparam_test.go`, which walks the whole registry
  (110 endpoints at time of writing) and **fails if it finds none**, so the
  test cannot pass vacuously after a regeneration that empties the registry.

- **Files:** `internal/mcp/code_orch.go` (executor + `pathPlaceholderNames`
  helper + `regexp` import); `internal/mcp/code_orch_pathparam_test.go`.

- **On reprint:** the press will regenerate `code_orch.go` without this. Re-apply
  it, and verify **by behaviour** — call a detail endpoint through MCP and check
  a real row comes back. Grepping for `pathPlaceholderNames` proves only that
  the symbol exists, which is the failure mode patch 0007's README warns about:
  presence is not correctness.

## Verification

```
$ echo '...tools/call jivo-factory_execute
        {"endpoint_id":"production-execution.run-detail","params":{"id":187}}' | jivo-factory-pp-mcp
{"id":187,"run_number":1,"date":"2026-08-11","line":3,"line_name":"10 Head",
 "product":"COLD PRESS GROUNDNUT OIL 1 LTR 16 PCS","item_code":"FG0000142", ...}

$ ... {"endpoint_id":"production-execution.run-detail","params":{}}
endpoint production-execution.run-detail needs path parameter(s) id —
pass them in params, e.g. {"params":{"id":"<value>"}}
```
