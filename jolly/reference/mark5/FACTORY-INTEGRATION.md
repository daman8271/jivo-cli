# MARK V factory integration — current evidence

Checked 10 September 2026, approximately 02:26 IST, against live **JIVO_OIL**.
Confidence: high for the read fields and deployed UI/source behavior below.
Plan creation, plan-check POST and production-start actions were not executed;
their backend effects and validation remain untested. This is integration research,
not an implementation or authorization to submit runs.

## The current page plans a run

Live authenticated `https://ji.jivo.in/production/execution/start-run` now displays
**Plan Production Run**, describes planning tomorrow's run with materials and clash
checks, and offers **Save plan**. The supplied screenshot's fields match this
current form: SKU, line, required cases/boxes, rated bottles/hour, production date,
planned start and optional manually chosen finish. Labour, other manpower,
supervisor and operators follow below. Selecting 10 Head also exposes required
line configurations and pre-fills their stored rate.

The deployed frontend separates these calls:

| Purpose | Method and path, relative to `https://factory.jivo.in/api/v1` | Evidence status |
|---|---|---|
| Check a proposed plan's material/timing conflicts | `POST /production-execution/runs/plan-check/` | Present in deployed JS; not called. |
| Save a production plan | `POST /production-execution/runs/` | Current Save plan handler calls `createRun`; not submitted. |
| Read saved plans and execution records | `GET /production-execution/runs/` | Verified live through CLI. |
| Read one record | `GET /production-execution/runs/{id}/` | Verified live, including run 343. |
| Start physical production recording | `POST /production-execution/runs/{id}/start-production/` | Separate deployed API action; not called. |

Do not equate Save plan with starting the machine or recording actual production.
The old June Mart page study is not the current Oil planning contract. The current
CLI has no create/start/plan-check command: this is a **missing CLI capability**,
not a permission restriction. Browser/app write code does exist. Whether MARK V
should submit factory plans is a separate user decision; this research creates none.

## Verified read contract

Use the VPS binary `/root/jivo-cli/factory-cli/jivo-factory-pp-cli.linux` with
`--company oil --data-source live --no-cache --json`. `doctor --json` reported
valid credentials and a reachable API. Its local synced cache was stale, so it
was not used. Company scope sends `Company-Code: JIVO_OIL`; the CLI otherwise
defaults to Mart. Do not omit the explicit company.

| CLI suffix after `production-execution` | API read path and useful fields |
|---|---|
| `lines` | `/lines/`: `id`, `name`, `is_active`, `standard_hours_per_day`, `standard_hours_per_month`. |
| `runs --date-from YYYY-MM-DD --date-to YYYY-MM-DD [--line-id ID] [--status STATUS]` | `/runs/`: `id`, `date`, `line`, `line_name`, `item_code`, `product`, `required_qty`, `rated_speed`, `pieces_per_case`, `litres_per_piece`, `planned_start_at`, `planned_end_at`, `planned_end_is_manual`, `planning_remark`, `status`, `live_status`, `total_production`, running/breakdown minutes, rejects/rework and warehouse approval status. |
| `run-detail --id ID` | `/runs/{id}/`: those fields plus `updated_at`, manpower fields, `machine_ids`, `segments`, `breakdowns`. Segment fields include `start_time`, `end_time`, `produced_cases`, `duration_minutes`, `is_active`, `is_manual`, `remarks`. |
| `line-configs --line-id ID` | `/line-configs/?line_id=ID`: stored SKU/pack presets; verify command help for filters. |
| `line-configs-auto-fill --line-id ID --sku-code CODE` | `/line-configs/auto-fill/`: wrapper `config` containing `id`, `line`, `config_name`, `sku_code`, `sku_name`, `rated_speed`, `pieces_per_case`, labour/manpower, supervisor/operators and active/timestamp fields. |
| `sap-items --search CODE --produced-only` | `/sap/items/?search=CODE&produced_only=true`: verified sample returned `ItemCode`, `ItemName`, `UomCode`; **not** a complete case/litre conversion. This is the factory form's SKU picker, not a substitute source for factory actuals. |
| `sap-bom --item-code CODE` | `/sap/bom/?item_code=CODE`: existing read command used by the deployed form. Current JS consumes `components[].ItemCode/ItemName/PlannedQty/UomCode`; this audit did not independently validate BOM scaling for a selected SKU. |
| `machines` | `/machines/`: live Oil response was empty. Do not infer physical machinery is absent. |

Runtime `agent-context --pretty` confirmed every production-execution command is
GET. It contains no planning-check/create/start or event-subscription command.
Read responses carry `meta.source: live` and `results`; preserve that provenance.
Use run `id` plus company as the durable identity, not date-relative `run_number`.

## Quantities, actuals and preset conflict

- Form `required_qty` is **finished-goods cases/boxes**. `rated_speed` is physical
  bottles/containers per hour. Do not send MARK V sales-unit pieces or litres as
  cases. Resolve the actual case mapping for each SKU; preserve missing units.
- For compatible source units, physical containers = cases × `pieces_per_case`;
  litres = containers × `litres_per_piece`. Neither null factor means zero or one.
  Mass packs need a sourced litre conversion. `UomCode: PCS` alone does not settle
  the case conversion: the FG0000461 picker says PCS, while its run records have
  `pieces_per_case: 20` and `litres_per_piece: 1`.
- Run 343 (9 September, 10 Head, FG0000461) has required 1,000 cases, recorded
  production 816 cases, 20 pieces/case, 1 L/piece and 436 running minutes.
  Its segments record 280 + 120 + 0 = **400 cases**, not 816. Keep run-total and
  segment evidence separate; do not sum them together or infer a production rate
  from the apparent one-minute segment with 280 cases. This is a current example
  of unresolved timing/quantity reconciliation, not a cause of downtime.
- Date-filtered reads for 8–10 September returned 12 runs, all with null planned
  start/end and blank planning remark. A separate 10–30 September read returned
  no rows at this check time. Fields exist; this sample does not demonstrate
  populated scheduling timestamps or assert there will be no later plans.
- The live 10 Head presets are 1 L 2,100/hour, 2 L 1,260/hour, 5 L 900/hour;
  auto-fill for line 3 and FG0000461 returned generic config 7 (`1 LTR`), blank
  SKU code and null pieces/case, with zero labour counts. Those are saved app
  defaults, **not** overrides of MARK V's approved PDF rates/routes, nor evidence
  of a zero-person crew. The live form requires a preset where configurations exist.
- Line master rows all contain 22 standard hours/day and 572/month. These are app
  master settings, not fresh roster evidence or permission to replace MARK V's
  shift/night constraints.

## Machine identity and pouch actuals

| Factory line ID | Factory name | MARK V mapping |
|---:|---|---|
| 1 | Clear Pack | Clear Pack |
| 2 | JP Machine | JP Machine |
| 3 | 10 Head | 10 Head |
| 4 | 6 Head | 6 Head |
| 5 | Pouch Machine | Unsplit pouch source identity |
| 6 | Tin Head | Tin Head |
| 7 | Manual | Manual evidence, outside the approved scheduled-machine scope |

All seven lines were active in the current Oil response. No separate Hitech or
Samarpan line was returned, and the machine list supplied no discriminator.
The 1–10 September line-5 run query returned no rows. Preserve an **unassigned
pouch actuals** identity until a verified run/asset mapping distinguishes the
machines. Do not assign every line-5 run to Hitech, duplicate it onto both machines,
or use the empty period to assert either physical machine made zero product.

## Deployed form checks and unknown backend behavior

The current JS builds plan-check input from `line_id`, `item_code`, required
cases, date, planned timestamps, manual-end flag, rated speed, optional preset
pieces/case and material-code/opening-quantity pairs. It calls the check after
SKU and a nonzero required quantity are present; filling both during a browser
inspection would issue a POST even without pressing Save plan. This audit left
that combination incomplete. The browser log contained 104 GET requests and no
POST/PATCH/PUT/DELETE at the final check.

Source-defined readiness states include `OK`, `TIGHT`, `CONTESTED`, `SHORT`,
`NO_STOCK_RECORD`, `UNKNOWN`. The form expects material rows, a timing result,
conflicts, and blocking flags `has_shortage`, `has_contention`, `has_conflicts`.
It requires a nonblank planning remark for shortage/contention and an explicit
clash acknowledgement before saving. These are deployed-client expectations;
the actual plan-check response and server-side enforcement were not exercised.

The Save plan payload includes selected SKU/product, `line_id`, date, required
quantity, rated speed, machine IDs, manpower, material entries and planned fields,
plus `acknowledged_warnings`. It does not explicitly send case/litre conversion
fields from the form schema; confirm server derivation before building a writer.
Do not invent an external-id/idempotency contract: none was established here.

The UI serializes a date/time as `YYYY-MM-DDTHH:mm` without an offset. Its manual
end validator rejects end times at/before the start on the same date. Backend
timezone handling and overnight scheduling must be verified before translating
MARK V's IST/cross-midnight sessions. Null planned time is not midnight or actual
start time. The form's “tomorrow” default also uses `toISOString()` after adding
a day; send an explicit production date rather than inheriting a browser default.

## Webhooks and practical integration

No factory run-event webhook/subscription capability was found in runtime CLI
discovery, local factory source/catalog search or the deployed production API
module. This is **not proof that no backend webhook exists**; no backend source
or subscription service was inspected. The CLI's `--deliver webhook:<url>` only
POSTs a command's resulting output to a supplied destination. It is not a factory
event subscription, and was not used.

Current feasible read integration is polling the verified runs/detail endpoints,
keeping each source timestamp/status and reconciling edits by company/run ID.
Retain last-good data visibly when a request fails; do not turn a failed read
into an empty run list. No polling frequency or concurrency was established by
this review. A future writer needs a CLI/API implementation, reviewed exact units,
read-back and duplicate prevention, and a clear distinction between plan save
and production start. It must not silently replace factory presets or bypass the
form's warning semantics.

Evidence files read: `factory-cli/AGENTS.md`, `README.md`, runtime doctor/help/
agent-context, `internal/cli/production-execution_{runs,line-configs-auto-fill,
sap-items}.go`, `internal/client/company.go`, `internal/cli/deliver.go`.
Current deployed assets: `StartRunPage-bE-zrqmu.js` (SHA-256
`a5c035e4b0e78cd29d4836970e8735d149dff79f48147db9f75b6b5da789f9bc`),
`execution.queries-Cev90XoK.js` and `execution.schema-BBM9TqeW.js`, with endpoint
constants in `index-BhPs7nos.js`. Browser used isolated VPS state
`/tmp/mark5-factory-browse.json`; copied browser authentication was cleared at end.
