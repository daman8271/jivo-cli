# Mark 4 data evidence — Codex independent discovery

Checked 6 September 2026, approximately 05:10–05:16 IST. Confidence: high for the live responses and local schema below; unresolved semantics are marked. No Claude Mark 4 implementation was inspected. The read-only factory CLI supplied all factory facts. No SAP CLI was called and no business record was written.

## Reproduce the reads

From the worktree repository root, source `.mark4-local/activate.sh`, then use `factory-cli/jivo-factory-pp-cli` with `--company oil --json --no-input --no-cache`. The commands below name the remainder. CLI discovery used `python3 hub/bin/hub.py search "factory machine speed labour cost bill of material"` and the `cli-hub` skill.

## Container and bottle weights

`production-execution sap-bom --item-code CODE` is the factory application's recipe endpoint. Envelope `results.components[]`: `ItemCode`, `ItemName`, `PlannedQty`, `UomCode`, `Warehouse`, `UnitPrice`. Quantities are **per carton**, not per individual bottle, in the checked groundnut examples. Divide by bottles per carton before using per-piece engine BOMs. Bottle weight and container type are in component names, not a dedicated weight field. Match primary container items, excluding `CAP`, `CARTON`, `STRIP`, labels and other accessories; the word TIN in `CARTON TIN TOP` must not create a second container.

The existing frozen baseline `sim/sep-inputs.aug31frozen.json` has `bom` as code-to-`[[component, quantity_per_piece], ...]`, `items` as code-to-`{name,uom}`, and `plan` as a **list**, not a mapping. This is old baseline evidence, not a current recipe fetch. Its containers independently support:

- PM0000076 `TIN 15 LTR`: FG0000191, FG0000015, FG0000275, FG0000132, FG0000158, FG0000367, FG0000026.
- FG0000232: PM0000260 `TIN 5 LTR SO OLIVE PRINTED`.
- FG0000043: PM0000113 `HDPE BOTTLE 3 LTR`.
- FG0000372: PM0000830 `TIN 3 LTR POMACE OLIVE PRINTED`.
- FG0000370: PM0000831 `TIN 3 LTR EXTRA LIGHT OLIVE PRINTED`.

The 15 L/5 L examples invalidate the sheet's PET label where it conflicts with the BOM. Routing still requires the clarified machine policy; a container match alone does not prove a measured machine speed.

## One verified 16 → 20 carton equivalence

Live factory BOM calls for **FG0000142 → FG0000461** prove the groundnut carton change precisely:

| Ingredient | Old case | New case |
|---|---:|---:|
| RM0000011 GROUNDNUT LOOSE OIL | 16 L | 20 L |
| PM0000121 PET BOTTLE 1 LTR 52 GMS POMACE | 16 | 20 |
| PM0000085 white/yellow logo caps | 16 | 20 |
| PM0000425 front groundnut label | 16 | 20 |
| PM0000426 back groundnut label | 16 | 20 |
| Carton | 1 × PM0000003, 16 PCS | 1 × PM0000914, 20 PCS 52 GM OLIVE |
| PM0000075 printed tape | 0.9652 m | 1.2 m |

Same oil, volume, bottle and labels. Pieces/litres remain unchanged when comparing fulfilled demand; cartons and BOM requirements change. Tape normalizes to 0.060325 vs 0.06 m per bottle. Do not merge arbitrary 16/20 SKU names across brand, oil, volume or customer-specific packaging. This is the **only pair live-verified in this bounded discovery**. Other equivalences need equally specific BOM evidence. New carton price is stored as zero; that does not prove free cartons.

Snapshots: `/tmp/mark4-evidence-bom-0142.json`, `/tmp/mark4-evidence-bom-0461.json`.

## Machine rated speeds

`production-execution line-configs` returned eleven active records, last modified 5 August:

| Line | Config | Bottles/hour |
|---|---|---:|
| JP | 1 L | 5400 |
| Clear Pack | 1 L | 4800 |
| Clear Pack | 5 L | 3000 |
| 10 Head | 1 / 2 / 5 L | 2100 / 1260 / 900 |
| 6 Head | 1 / 2 / 5 L | 1080 / 720 / 600 |
| Pouch | Hitech / Samarpan | 1800 / 2400 |

Fields: `line`, `line_name`, `config_name`, `rated_speed`, `pieces_per_case`, `labour_count`, `other_manpower_count`, `is_active`, timestamps. No Tin Head, 3 L, or 4 L configuration exists in this response. All staffing presets are zero and pieces-per-case null: missing defaults, not evidence of unmanned production. Two pouch configurations do not establish two simultaneous staffed sessions.

Clear Pack 5 L is **3000 rated**, unlike the frozen 1000 basis. User's 80% policy acts once on the selected disclosed capacity basis. Do not silently preserve an old 50% derating and then multiply by 80%. `production-execution lines` still stores 22 h/day and 572 h/month; those are superseded for this planner by Daman's clarified 10 working hours/session and one optional night line. Snapshot `/tmp/mark4-evidence-line-configs.json`, `/tmp/mark4-evidence-lines.json`.

## Labour: usable actual run costs, missing verified session rate

- `production-execution cost-rates`: **HTTP 404** today.
- `production-execution reports-analytics-cost-analysis --date-from 2026-09-01 --date-to 2026-09-06`: succeeded, `results.per_run[]` has `run_id`, `date`, `line`, `product`, `item_code`, `produced_qty`, `litres`, `labour_cost` and other component costs.
- Twenty-one recorded runs. Observed labour-cost range: main lines ₹11,700–₹12,120.16/run; Tin Head one run ₹6,843.24. These are source **run costs**, not an established ten-hour session price. Window/run coverage must accompany any display.
- `production-execution run-labour --id 295` gives 18 workers, `hours_worked=1`, `rate_per_hour=0`, `total_cost=0`. Run 312 gives ten workers with the same zero rate/cost. These entries disagree with the nonzero analytics amounts; do not treat the zero records as free labour.
- `production-execution run-detail --id 295` has `labour_count=18`, `rated_speed=4800`, timing segments, but no wage-rate fields. Several segments record production in zero or one minute; typical speed calculated from these cannot be promoted to a clean capacity measurement without validation.

Recommended honest V1: show recorded recent run labour cost separately from **session labour estimate unavailable — rate/paid-hours basis not verified**, or make a distinctly labelled user-entered scenario rate. Do not invent a session rate by dividing run cost by corrupted segment duration. No staffing/wage system was mutated.

Snapshots `/tmp/mark4-evidence-cost-analysis.json`, `/tmp/mark4-evidence-run-labour295.json`, `/tmp/mark4-evidence-run-labour.json`, `/tmp/mark4-evidence-run295.json` (run snapshots may contain personnel: never publish raw).

## OMS trailing demand

Live `oms-cli/oms-pp-cli orders dashboard-charts --config "$OMS_CONFIG" --json --no-input --no-cache` failed **401 token_not_valid / Token is expired** using the isolated copied config. No login/refresh mutation was made during this subtask. The parent can restore isolated authentication through the supported login flow.

Verified source/code guidance, not new live sales totals:

- `orders detail ID`: header creation/order dates, category/company/status and line-level item code, qty, pcs, boxes and ltrs. Exact existing parser and incremental cache: `live/adapters/oms.py`.
- `orders by-item --item-code CODE` is an ID index only; no quantities/dates in documented response. Fetch matching details to compute history.
- `orders list`, dashboards and dashboard charts are account/role-scoped. They cannot prove the company's complete trailing GT/MT demand. The existing adapter walks IDs; inspect its cache coverage metadata before using it for months of history.
- Orders are **orders**, not realised sales. A trailing order-volume forecast should say so, filter rejected/draft/cancelled cases appropriately, scope Oil, and exclude e-commerce explicitly where supported. Do not describe monthly plan targets as a computed trailing OMS average.
- The user approved OMS as the demand source but did not settle three vs six historical months. That window must be a disclosed planner choice, and only months with verified complete coverage can support it.

## Dispatch aging

Live `dispatch-plans bills --date-from 2026-08-01 --date-to 2026-09-06 --company oil` returned `results.data`, `results.meta`, `results.pagination`: 789 rows, 1 page, fetched_at 2026-09-05T23:45:30.208494+00:00. Metadata: 435 pending, 354 dispatched. Current output differs from older docs using other envelope names.

Needed fields: `doc_date`, `doc_num`, `total_litres`, `warehouses`, `plan.booking_status`, `plan.pipeline_status.stage`, `plan.dispatch_date`. Age = planning date minus **invoice `doc_date`**, not planned dispatch date or stage-change timestamp. Display invoice-window coverage. `company_code` is null on all rows in this scoped response; request used Oil but the payload does not independently attest company. Branches include FACTORY/DELHI/PUNJAB. Warehouse filter is necessary for a factory-storage view.

Crucial: these are **undispatched bill records**, not a reconciled physical pile. Summing old PENDING bills can grossly exceed the godown's physical stock (the historical C-0076 trap). Use them for pendency of the open bill book with coverage caveats, never replace physical storage arithmetic with their total. A 1 August start cannot prove older open bills absent. All-time fulfillment-summary backlog also has different semantics from windowed bills.

Snapshot `/tmp/mark4-evidence-dispatch-bills.json` contains contacts and addresses: **never publish raw**. Export an aggregate or a field-allowlisted, masked record list only.
