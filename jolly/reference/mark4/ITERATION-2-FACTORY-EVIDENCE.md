# Mark 4 second iteration: factory evidence and independent supplement

Checked live on 6 September 2026, beginning 06:12 IST. Factory reads only, scoped `JIVO_OIL`. No SAP CLI, business write, existing collector, cron, or service change. Confidence: high (approximately 99%) for returned fields and computed aggregates; supplier-delivery timing is unknown. Original checkout and Claude's independent Mark 4 were not edited.

## Completed full-catalog verification

At 06:24–06:25 IST the independent worker finished all **2,231 / 2,231 Oil vendor-catalog reads**, zero failures. It found **324 open purchase orders / 758 lines across all purchasing categories**. The safe published material subset is **129 orders / 220 lines: 201 packaging and 19 raw-material lines**, dated 26 November 2024 through 4 September 2026. Other goods, services, fixed assets and finished-product purchasing are excluded from the material ledger. Delivery dates remain absent.

Full coverage changes the white/yellow-logo cap balance (PM0000085) to **11,48,000 PCS**, versus 8,98,000 in the initial 18-supplier sample. The 52 g bottle remains 78,176 PCS, and the 26 g bottle remains 9,85,128 PCS. The checked-in fixture now matches the live `{asOf,ok,data}` envelope, captured 06:25 IST, rather than the initial bounded sample below. `coverage.materialOrderCount` and `materialLineCount` are the numbers to use on a materials UI; `openOrderCount` is source-wide and includes unrelated purchasing.

The initial complete worker was PID 1326314, interval 180 seconds; first complete refresh using cached PO evidence took 1.3 seconds. Supplier PO evidence has its own `poAsOf` (06:24 IST). Response hardening rejects HTTP redirects, only accepts approved HTTPS factory hosts and `/api/v1`, and bounds each response to 16 MiB before parsing. A failed-refresh regression verified that the last-good data and original `asOf` survive with `ok:false`.

## What explains the late-month production gaps

Existing `live/freeze_live.py` explicitly says packaging already on order is missing from arrivals. Its packaging backlog is not a dated delivery feed. The schedule can exhaust current packaging despite real purchase orders remaining open. That is a data limitation, not evidence the factory will actually stop.

The initial bounded read covered all 40 September gate entries, one page, and all 18 suppliers appearing on those entries. Their factory `po open-pos` calls returned 63 open orders and 120 lines, zero failed requests, with order dates from 25 January 2025 through 4 September 2026. Examples of remaining order quantities:

| Material | Ordered balance | Unit |
|---|---:|---|
| PM0000121 — 52 g 1 L bottle | 78,176 | PCS |
| PM0000851 — 26 g 1 L bottle | 9,85,128 | PCS |
| PM0000085 — white/yellow logo cap | 8,98,000 | PCS |
| PM0000053 — 5 L HDPE bottle | 1,43,246 | PCS |

These are open purchase-order balances, not physical stock or committed delivery dates. The independent collector now enumerates the entire factory Oil vendor catalog to extend this bounded sample; its output coverage fields give the actual completed supplier count and total catalog count. Do not quote the initial 63-order sample as the entire Oil book after the full-catalog result is available.

## No supplier ETA field was found

`GET /po/open-pos/?supplier_code=...` returns a list of order headers with `po_number`, `doc_entry`, `branch_id`, `supplier_code`, `supplier_name`, `vendor_ref`, `doc_date`, `items`. Each item has `po_item_code`, `item_name`, `ordered_qty`, `received_qty`, `remaining_qty`, `uom`, `rate`, `line_num`. Quantities and rates are decimal strings. There is no due date, promised date, expected date, delivery schedule, or destination warehouse in this response. Preserve units: MTS oil is not LTR, and PCS preforms are not finished bottles.

Two tempting endpoints do not supply the missing promise:

- `GET /planning-purchase/purchase-orders/` succeeded with `data` and `meta`: two records, both CANCELLED. It has `doc_date` and `doc_due_date`, but neither order is eligible to receive stock.
- `GET /planning-purchase/commitments/?item_code=...&warehouse=...` means **reservations against stock**, not supplier commitments. It requires both query parameters. Its records are production orders, transfer requests, and sales reservations, with `planned_qty`, `issued_qty`, `committed_qty`, `due_date`, and `is_stale`. For the 52 g bottle in BH-PM, all 17 reservations are stale transfer requests; their dates cannot become inbound dates. Header `on_order_qty=78176` independently matches the sampled 52 g bottle PO balance.

Do not estimate lead time from PO creation to gate arrival. Existing `factory_inbound.py` documents that these are blanket contracts drawn down in many partial loads. That age measures contract age, not supplier manufacturing/transit lead. Undated POs should be visible with an editable, explicitly hypothetical expected receipt date. They must not silently appear in stock today or be called supplier-confirmed.

## Gate acceptance and double-counting

The September GRPO page returned `count=40`, `total_pages=1`: one GATE, six QC, 33 DONE entries. `po_receipts[].items[]` exposes received, accepted, rejected quantities, units and QC status; each receipt has `is_posted`. The same material can appear on an open PO and already at the gate.

- Pending QC comprises seven material lines on six entries: 160.09 MTS soybean oil plus 15,972 PCS packaging. A tanker arrival is not its quality-release date.
- Seventeen ACCEPTED rows have `accepted_qty=0` but positive received quantity. The established factory rule is usable = received minus rejected **only when `qc_status == ACCEPTED`**. Zero accepted_qty does not prove rejection or no receipt.
- Opening physical stock must not be increased by replaying accepted or posted historical receipts. The supplement exposes these as audit records, not future-arrival events.
- Before calculating a PO's not-yet-at-gate balance, deduct its unposted gate receipts by PO and item. Deductions are allocated once across matching order lines. This reconciliation covers the current-month gate window; older unposted receipts might still require reconciliation. The public ledger retains both the raw remaining balance and the deducted quantity.
- Raw-material PO events can duplicate EXIM contracts. The periodic supplement emits packaging PO events and raw-material reference events. Raw-material reference events have `stockIncluded:null` and an explicit EXIM-overlap note, making them ineligible for date overrides or additional stock credit until reconciled. QC events remain separate and require a verified or scenario quality-release date.

## Recorded labour is available per machine

Live `production-execution reports-analytics-cost-analysis --date-from 2026-09-01 --date-to 2026-09-06` returned 21 costed runs, dated 1–4 September:

| Machine | Runs | Mean recorded labour per run | Range |
|---|---:|---:|---:|
| 10 Head | 7 | ₹11,862.75 | ₹11,700–₹12,103.26 |
| 6 Head | 4 | ₹11,948.98 | ₹11,817.13–₹12,119.58 |
| Clear Pack | 4 | ₹11,954.37 | ₹11,853.85–₹12,119.58 |
| JP Machine | 5 | ₹11,927.97 | ₹11,813.64–₹12,120.16 |
| Tin Head | 1 | ₹6,843.24 | one recorded run |

Manual and Pouch have no costed runs in this window, represented by null rates and zero sample count. Do not present them as free. `cost-rates`, including `scope=global`, still returns HTTP 404. Existing run-labour evidence has zero direct wage fields despite the nonzero analytics costs. The useful display is **recorded labour per run, 1–4 September**, with sample counts. This is not a verified ten-hour session wage, and repeated runs in a day cannot be assumed to mean separately paid crews.

## Historical production quantity and worth

The daily MES endpoint and cost analytics do not agree on quantity. All 27 returned runs on 1–5 September have `total_production` different from the sum of `segments[].produced_cases`. Cost analytics uses the header quantity; existing Mark 3 production history uses segments. On 5 September all six headers are zero while segments yield 58,080 L. Keep existing segment arithmetic for the MES composition; do not replace it with labour analytics quantities or silently overwrite headline actuals.

The normalization reuses the established `_day_rows` and `_booked` functions from `live/adapters/factory_production.py`. MES case litres use the factory fields `pieces_per_case × litres_per_piece` before parsing the SKU name. In some runs the app uses `pieces_per_case=1` and `litres_per_piece=20` for a whole case; name-only parsing would be wrong by tenfold.

A separate live factory movement read succeeded:

```
production-execution reports-production-movement
  --date-from 2026-09-01 --date-to 2026-09-05
  --warehouse BH-PF --transaction-type 59 --limit 1000
```

It returned 45 rows, below the cap, with `date`, `item_code`, `in_qty`, `transaction_value`, `transaction_type`, and warehouse. This is the factory's book/stock transaction value on the receipt date. The API has no per-row currency field; INR is the factory report's documented rupee denomination (`factory-cli/app-model/sections/08-production.md`, production-movement report), consistent with the project's established INR contract. It is **not sales revenue or a selling-price valuation**. Confidence high in value semantics and arithmetic; denomination relies on the report/system contract rather than a currency field in each record.

| Receipt date | MES litres (segments) | Booked receipt litres | Booked transaction value |
|---|---:|---:|---:|
| 1 September | 1,13,524 | 729 | ₹1,08,223.71 |
| 2 September | 28,760 | 84,758.780 | ₹2,01,38,661.44 |
| 3 September | 1,00,135 | 52,501.291 | ₹1,08,14,116.99 |
| 4 September | 16,600 | 1,12,945.692 | ₹1,78,33,538.16 |
| 5 September | 58,080 | 69,192 | ₹1,09,03,529.86 |

Book receipts lag production, so these columns must remain separate. To compare historical production worth with the future ₹ target, apply the **same disclosed per-SKU selling-realisation basis** to historical MES or booked quantity composition and label it estimated worth. Show recorded transaction value as a separate detail, with its own basis. `booked_by_item` remains pieces; `mes_by_item_l` is litres.

## Files and source contracts

- `site-mark4/data/iteration-2-factory-evidence.json`: sanitized full-catalog evidence fixture in the exact live envelope. No personnel, contacts, vendor names, or raw document numbers. Public line/order identities are stable SHA-256 prefixes.
- `site-mark4/scripts/factory_source.py`: pure allowlisted normalizer. Reuses existing production parsing, without executing the original collector.
- `site-mark4/scripts/collect_factory_supplement.py`: independent GET-only collector. Fixed allowed paths; copied auth; private raw cache; complete pagination; full vendor catalog scan; four request workers maximum; explicit caps fail instead of publishing truncated truth.

Live isolated paths:

```
/root/mark4-astha/revision2-factory/collect_factory_supplement.py
/root/mark4-astha/revision2-factory/factory_source.py
/root/mark4-astha/revision2-factory/research-auth.json      # PRIVATE, mode 600
/root/mark4-astha/revision2-factory/cache/                  # PRIVATE
/root/mark4-astha/revision2-factory/collector.log
/root/mark4-astha/state/factory-supplement.json
```

Collector command:

```
MARK4_FACTORY_REFERENCE_ROOT=/root/jivo-courier/jolly python3 \
  /root/mark4-astha/revision2-factory/collect_factory_supplement.py \
  --config /root/.config/jivo-factory-pp-cli/config.toml \
  --cache-dir /root/mark4-astha/revision2-factory/cache \
  --output /root/mark4-astha/state/factory-supplement.json \
  --interval 180
```

The source reference is read-only. No original collector is invoked. Omit `--interval` for one bounded cycle. PO/catalog refreshes are cached independently, with original read times; a failure retains the previous whole supplement and its original `asOf`, setting `ok:false` and a generic error. Auth failures do not trigger writes or refreshes against the shared source session. This private worker was started with nohup; no existing system service was changed.

Output: `{asOf,ok,error?,data}`; `data` contains `inboundEvents`, `recordedLabour`, `historyDays`, `coverage`, `openOrderLines`, `outstandingByItem`, `gateReceipts`, `sourceStatus`, `sourceDisagreements`. Historical rows include `mes_by_item_l`, `booked_by_item`, `booked_by_item_value_inr`, and `booked_recorded_value: {value,coveredLitres,asOf,basis,rows}`. The feed owner must preserve each source's timestamp and coverage, merge by date, and never make missing/failed data zero.


## Independent revision-two functional audit, pass 1

The new collector now reads `/root/.config/jivo-factory-pp-cli/config.toml` **on every request**, without writing to it or rotating any refresh token. The existing factory CLI keepalive updates this default config through its own login. The file is TOML; observed keys are `base_url`, `access_token`, `auth_header`, `client_id`, `client_secret`, `factory_token`, `refresh_token`, `token_expiry`. No values were logged. Worker PID 1342173 uses that current file; a subsequent read cycle was successful. The old private research-auth copy is no longer the worker's auth source.

The full live fixture now carries **227 inbound references: 201 PM PO lines, 19 RM PO lines, and seven QC material lines**. RM PO references have `stockIncluded:null` and retain their source units; they are visible but cannot be converted into duplicate EXIM supply. Their date override is rejected explicitly.

An independent test suite was added at `site-mark4/tests/test_factory_revision_acceptance.py`; it imports the existing TypeScript evidence/model functions through Node type stripping, and does not modify them. It ran on isolated VPS `/root/mark4-astha/factory-qa`, **15 cases passed in 1.035 seconds**:

1. Booked pieces convert through the correct per-SKU pack size and use the same current price as future production.
2. MES composition is already litres and is not multiplied by pack size again.
3. Missing prices, missing pack conversions, and unreconciled source totals cannot headline a complete valuation.
4. Observed zero remains zero; unread remains unavailable.
5. All 21 costed factory runs reconcile by machine, totaling ₹2,45,135.79; absent Pouch costs remain null.
6. Labour records deduplicate by source ID without deleting legitimate identical rows lacking IDs.
7. Undated live factory POs remain visible with no stock credit.
8. One selected packaging arrival override credits exactly its outstanding line, conditionally.
9. Duplicate inbound IDs count once; conflicting records with the same ID fail.
10. MTS oil and unresolved EXIM overlap cannot receive assumed dates or litre credit.
11. Received, cancelled, and opening-stock-included records reject date overrides.
12. Invalid calendar dates, out-of-month dates, and outdated IDs fail explicitly.
13. Recorded transaction values reconcile by SKU and stay separate from MES quantities.
14. Remaining PO quantity equals unposted-at-gate plus not-yet-at-gate, without duplicate IDs.
15. A full planner run applies the selected receipt exactly once and passes its stock invariants.

**Findings:** no functional failure in this bounded engine audit. This proves these arithmetic and scenario cases against the tested TypeScript snapshot and full factory fixture. It does not independently verify the browser rendering or the parent's final feed merge; those need the subsequent end-to-end pass.


## Independent revision-two functional audit, pass 2: merged candidate

The second audit uses `/root/mark4-astha/state/merged-candidate.json`, with the actual factory and demand supplements plus seven EXIM transit references. The 15-case TypeScript acceptance suite was rerun against this merged input through `MARK4_ACCEPTANCE_INPUT`, rather than substituting the old seed. **15 cases passed in 1.760 seconds.** The audit also compared every priced historical SKU with its forward-plan price; **zero parity differences** were found. No engine or UI files were changed by this reviewer.

### Finding P2 — rice kilograms converted as oil litres

The first candidate carried `valuation.litresPerPiece.FG0000224=1.0989010989` for `JIVO RICE 1 KGS 4 PCS`. That is the generic kilogram/0.91 oil-density conversion applied to rice. Eight booked pieces on 3 September consequently appeared as 8.791 litres, and the engine described that pack conversion as verified. The estimated rupee value was already partial because no selling price exists, but the volume conversion and provenance label were wrong. Recommended fix: exclude non-oil kilogram packs from oil-litre valuation; keep original source quantity/book value visible, and mark the litre composition unresolved. The parent implemented this guard in the merger; verification against the regenerated candidate is recorded below when available.

### Missing selling prices were not pruned by the merger

Directly compared the live original `sim/live-inputs.json` and merged candidate: both have exactly 127 realisation keys, with identical values for the missing historical SKUs. The earlier August-31 frozen table independently has the same gaps:

| SKU | Source selling price | Effect |
|---|---|---|
| FG0000224 — rice 1 kg | absent | no oil-litre selling valuation |
| FG0000104 — extra-light olive 100 ml | 0 | treated as unavailable, not free |
| FG0000154 — mustard 100 ml | 0 | treated as unavailable, not free |
| FG0000105 — extra-light olive 250 ml | 0 | treated as unavailable, not free |
| FG0000362 — La Rasoi canola 2 L | absent | 3,920 booked litres on 4 September unpriced |
| FG0000461 — new 20-piece groundnut | absent directly | inherits ₹168.75/L only through the verified FG0000142 transition |

All five MES days have full per-SKU selling-price coverage under the current inherited price basis. Booked selling-worth coverage is complete on 1, 2 and 5 September; 3 and 4 September remain partial for the reasons above. The price date is explicitly null and the basis explicitly says inherited realisation, not dated sales or booked cost. Recorded factory transaction values remain separate, and match their source values.

### Labour and incoming supply

The merged candidate preserves all 21 recorded labour runs, the same ₹2,45,135.79 aggregate, and null Pouch cost; every machine total reconciles to the source. Labour's cost-per-litre denominator comes from the paired cost analytics run, not the conflicting MES segment quantities.

Of 234 incoming references, six EXIM shipments are credited on their future dates. The seventh, 42,945.01 L of soybean oil expected 5 September, stays excluded as overdue rather than being moved to today. All 19 raw-material PO references retain `stockIncluded:null` and receive no stock or procurement credit. All 201 undated packaging PO lines and seven pending-QC material lines are visible without automatic stock credit. A chosen compatible packaging-date override adds that line exactly once, conditionally; unit mismatches, received/cancelled lines and unresolved overlaps reject overrides.

This audit covers the candidate's data and TypeScript behavior. The parent's browser pass remains responsible for rendering, navigation and persistence.


### Live factory product identities and durable refresh

Three exact live `production-execution sap-items --search CODE --company oil` lookups confirmed:

- FG0000328: **SANO POMACE OLIVE 200 LTR 1 PCS**.
- FG0000275: **COLD PRESS SUNFLOWER OIL 15 LTR**.
- FG0000005: **EXTRA LIGHT OLIVE 1 LTR 16 PCS**.

All report UomCode PCS. E-commerce rows using those same codes for 1 L yellow mustard, 2 L sunflower, or another olive grade cannot be joined on code alone. The original frozen `items` dictionary is not a current identity authority (`freeze_live.py` inherits it from the baseline).

A fresh company-qualified factory barcode catalog now supplies **371 FG identities** at `/root/mark4-astha/demand-audit/factory-identity.json`. `barcode items-oitm --search FG --limit 2000` silently returned its hard cap of 200, so the complete bounded collection queries ten disjoint prefixes `FG00000` through `FG00009`. Returned prefix counts were 81, 89, 56, 82, 63, 0, 0, 0, 0, 0, all below the cap. This covers FG0000000–FG0000999 and all 69 FG codes reported by the current demand-source audit. It does not claim codes outside that range.

Catalog fields: `name`, `uom`, `groupCode`, `piecesPerBox`, `piecesPerBoxSource`, `validFor`, `frozenFor`, `company`. No pack-litres value is invented. The demand-source owner verifies name, oil grade and pack against this factory identity, quarantining collisions and unknowns.

The independent factory collector now accepts `--identity-output /root/mark4-astha/demand-audit/factory-identity.json` and refreshes the catalog every **12 hours**, using the current factory CLI auth read-only. Its `asOf` is the oldest prefix read and is not refreshed by merely reusing the cache. A failed refresh keeps the previous items and timestamp but sets `ok:false`; consumers must require both non-failed status and age within 24 hours. Successful refresh and failed-refresh retention were checked with deterministic fake reads. The CLI allowlist includes only the GET barcode item path added for this purpose; redirect and response-size protections remain active.


### Final pass-two recheck after the fixes

The regenerated **06:39 IST candidate** was tested with the latest `identity.ts`, `evidence.ts`, and `model.ts`. All **15 acceptance cases passed again in 2.650 seconds**. The rice finding is fixed: FG0000224 has no litre-pack mapping, its historical line says `litres:null` / `Pack conversion unavailable`, and 3 September booked value stays partial with unreconciled composition. The original source receipt aggregate is retained transparently rather than silently rewritten.

Current identity-quarantine logic leaves all five MES-day selling-worth valuations complete because those actual priced SKUs are not among the conflicting inherited planner identities. Booked 1, 2 and 5 September remain complete; booked 3 and 4 September remain partial due to the proved source gaps. Historical versus forward price parity remains exact for every shared priced SKU. All 234 incoming references reconcile: six future EXIM arrivals receive expected stock credit, one overdue EXIM row is held, 19 raw-material PO references receive none. Labour still reconciles all 21 runs.

No unresolved functional finding remains in this bounded source/engine audit. Deployment note sent to the parent: the promoted factory worker must receive the latest collector file and `--identity-output` flag before continuous identity refresh is claimed; the currently captured catalog is already fresh and verified. Browser behavior remains the parent's independent responsibility.
