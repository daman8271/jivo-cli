---
title: "0010 — add three live-verified GET endpoints (scan-lookup, QC run sessions, PO receipts view)"
created: 2026-08-31
updated: 2026-08-31
project: jivogpt
type: patch
tags: [jivogpt, factory, cli, printing-press, patches]
---

# 0010 — Add three live-verified GET endpoints, and correct one wrong param description

## Contract

Three GET endpoints and one corrected `id` param description, hand-applied to the
generated tree from `spec.yaml`. Re-apply on reprint if the generator has not picked
them up from the spec.

| Endpoint | Command | Status |
|---|---|---|
| `GET /maintenance/scan/lookup/` | `maintenance scan-lookup` | shipped |
| `GET /quality-control/production-qc/runs/{id}/sessions/` | `quality-control production-qc-run-sessions` | shipped |
| `GET /raw-material-gatein/gate-entries/{id}/po-receipts/view/` | `gate-core raw-material-gate-entry-po-receipts` | **shipped, but violates `research/verify-invariants.sh` — see Open conflict** |
| `GET /gate-core/raw-material-gate-entry/{id}/` | `gate-core raw-material-gate-entry` | param description corrected |

READ-ONLY holds: `spec.yaml`, `tools-manifest.json` and `codeOrchEndpoints` all declare
483 endpoints, every one `GET`. No POST/PATCH/PUT/DELETE was added. `POST
/maintenance/scan/work-order/` — the write twin of `scan-lookup` on a different path —
was deliberately NOT generated.

## Why the tree was hand-edited rather than reprinted

A full reprint was rejected, not skipped:

1. The installed `cli-printing-press` is **v4.24.0**; the published currency floor
   (`supported-versions.txt`) is **v4.28.0** and latest is v4.31.3. Regenerating below
   the floor reproduces since-fixed generator bugs.
2. Upgrading and reprinting would rewrite the whole tree across seven minor versions of
   template drift, and this workspace has **no `.printing-press.json` base run id** (see
   this directory's README) — so there is no baseline to merge against and patches
   0001-0009 would all have to be re-proved by hand anyway.
3. The ask was three endpoints. The blast radius of a reprint is the entire CLI.

Every edit below therefore mirrors the generator's own emitted shapes byte-for-byte
(command template, `codeOrchEndpoint` literal, manifest tool object).

## Files touched

- `spec.yaml` — 3 endpoints added, 1 param description corrected (source of truth)
- `internal/cli/maintenance_scan-lookup.go` — new
- `internal/cli/quality-control_production-qc-run-sessions.go` — new
- `internal/cli/gate-core_raw-material-gate-entry-po-receipts.go` — new
- `internal/cli/{maintenance,quality-control,gate-core}.go` — `AddCommand` registration
- `internal/cli/which.go` — 3 capability-index rows
- `internal/mcp/code_orch.go` — 3 `codeOrchEndpoints` entries (the registry a rescrape
  historically forgets, which makes agents see `unknown endpoint_id`)
- `internal/mcp/tools.go` — 3 group `endpoints` list additions
- `tools-manifest.json` — 3 tools + the corrected description (480 -> 483)
- `README.md`, `SKILL.md` — 3 command rows each
- `research/verdict-kills-2026-08.json` — removed
  `/quality-control/production-qc/runs/{run_id}/sessions/`; it was a bare string with no
  stated reason and was re-probed and cleared (51 -> 50 kills)

## Evidence (live, 2026-08-31, JIVO_OIL unless stated)

```
$ jivo-factory-pp-cli maintenance scan-lookup --code ZZZ-NOPE --company oil
Error: GET /maintenance/scan/lookup/ returned HTTP 404:
{"found":false,"code":"ZZZ-NOPE","detail":"No maintenance asset or spare matched this code."}

$ jivo-factory-pp-cli quality-control production-qc-run-sessions --id 179 --company oil
200, 1 row: id 9, run 179, "COLD PRESS GROUNDNUT OIL 1 LTR 16 PCS", session_type FINAL
  --session-type FINAL     -> 1 row
  --session-type INPROCESS -> 0 rows
  --company mart           -> 404 {"detail":"No ProductionRun matches the given query."}

$ jivo-factory-pp-cli gate-core raw-material-gate-entry-po-receipts --id 4176 --company oil
200, 1 row: id 1199, PO 220826134, EAST INDIA DRUMS AND BARRELS,
  is_editable false, lock_reason "This PO cannot be edited after its arrival slip is
  submitted to QC.", items[0] PM0000073 MS COATED DRUM 200 LTR 100/100 PCS @1850
  --company mart -> 404 {"detail":"No VehicleEntry matches the given query."}
```

`gofmt`, `go vet ./...`, `make build`, `go test ./...` all clean; MCP guard tests pass.

## Open conflict — `/po-receipts/view` is on this repo's never-publish list

`research/verify-invariants.sh` section 2 fails after this patch:

```
FAIL  PUBLISHED (2x): /po-receipts/view
```

That gate is **not a stale leftover**. `MIGRATION-2026-08.md` excludes it with a reason:

> `security-checks …/security/view`, `weighment …/weighment/view`, `raw-material-gatein
> …/po-receipts/view` — Same `get_or_create` shape: a child record keyed by its parent's
> gate-entry id. Never probed, because the only way to test is to call one for a parent
> with no child, which is the act that would create it.

The precedent is real: `GET /marketplace/settings/` is a confirmed Django `get_or_create`
that created six junk production rows on 2026-08-03 (correction **C-0007**, patch 0007).

What the live verification of id 4176 does and does not prove: 4176 **has** a receipt, so
it exercises only the has-child path — exactly the case the exclusion says looks safe and
proves nothing. Nothing in the verification touched a childless parent.

Zero-risk evidence in this repo that points the other way, gathered without probing:

- `research/refute-factory-2026-08-22.md` recorded `/po-receipts/view/` on entry 3707
  returning a JSON **array** (`[{"id":1087,...}]`). A `get_or_create` returns one object;
  a `many=True` list serializer cannot create.
- Its sibling `/weighment/gate-entries/3707/weighment/view/` returns
  `404 {"detail":"Weighment not found"}` for a parent with no child — that family 404s on
  a miss, it does not fabricate.
- `DOMAIN-GUIDE-2026-08.md` puts confidence that this /view/ family is safe at ~85%, and
  says the residual doubt is that a GET-only `Allow` header does not discriminate — the
  marketplace `get_or_create` also lived inside a GET handler.

Marginal value is small: `DOMAIN-GUIDE-2026-08.md` names `gate-core
raw-material-gate-entry` as the "zero-risk substitute" that returns the same receipts
nested. The only fields this command adds are `is_editable`, `lock_reason` and
`updated_at`.

**The gate was left red on purpose.** Editing `verify-invariants.sh` to make the FAIL
disappear would launder an unresolved side-effect risk. Two ways to close it, both a
human's call:

1. Read the Django view source for `PO_RECEIPTS_VIEW` — settles it at zero risk.
2. Deliberately GET a raw-material gate entry known to have **no** po-receipts. `[]`
   proves a plain filter; a returned row means one was created. This is the probe the
   repo's own rule forbids without an explicit go-ahead.

Until one of those happens, treat `gate-core raw-material-gate-entry-po-receipts` as
shipped-but-unproven, and prefer `gate-core raw-material-gate-entry`.

## Known pre-existing quirk (not fixed here)

Cobra reads the first back-quoted word of a flag's usage string as the flag's type
placeholder, so a param description containing `` `grpo all-entries` `` renders as
`--id grpo all-entries` instead of `--id string`. **52 existing flags** across this CLI
are affected. The three new flags use single quotes instead so they render `string`.
Fixing the other 52 is a generator-template fix and belongs upstream, not here.

## Reprint checklist additions

10. Confirm `spec.yaml` still declares `maintenance.scan-lookup`,
    `quality-control.production-qc-run-sessions` and
    `gate-core.raw-material-gate-entry-po-receipts`, and that
    `gate-core.raw-material-gate-entry`'s `id` description names
    `grpo all-entries`.results[].vehicle_entry_id (NOT the dead
    `/raw-material-gatein/gate-entries/` route).
11. Confirm `codeOrchEndpoints` in `internal/mcp/code_orch.go` carries all three — a
    rescrape updates the CLI and the manifest but has historically missed this registry.
12. Re-check the Open conflict above before treating a green
    `research/verify-invariants.sh` as meaningful.
