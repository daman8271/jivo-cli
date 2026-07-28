---
endpoint: /realise/api/sales-cn/
method: POST
auth: session + X-CSRFToken (JSON body)
readonly: true
used_by: [sales-cn]
tags: [jivo, api, sales, credit-notes]
---
# `POST /realise/api/sales-cn/`

## Purpose
Returns line-level **gross sales vs credit-note** rows for one company (Oil or Beverages) over a date range, so the [[sales-cn]] page can pivot Total Sales, Total CN, and Net Sales by any dimension. Powers the whole "Sales vs Credit Notes" report — the pivot, KPIs, and Excel export are all built client-side from this one flat row list.

## Request
JSON body (`Content-Type: application/json` + `X-CSRFToken`):

| Field | Type | Meaning |
|---|---|---|
| `start_date` | `YYYY-MM-DD` | Range start (inclusive). Page defaults to 1st of current month. |
| `end_date` | `YYYY-MM-DD` | Range end (inclusive). Page defaults to today. |
| `company` | `"oil"` \| `"beverages"` | Which company's books. Toggled by the Oil/Beverages segment. Default `oil`. |

The page sends only these three fields. All filtering (Premium/Commodity type, search, drill dimension, Revenue/Litres measure) is done **client-side** on the returned rows — no extra params.

## Response
HTTP 200 · `Content-Type: application/json`. Top-level keys:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"` or `"error"` (with `error` message). |
| `company` | string | Echo of requested company. |
| `measure` | string | Quantity unit label for this company — `"Litres"` (oil) or `"Boxes"` (beverages). Drives the Litres/Boxes button label. |
| `has_type` | bool | Whether Premium/Commodity classification applies. `true` for oil, `false` for beverages (hides the Type filter). |
| `rows` | array | One row per (customer × item × group × state × type) aggregate. |
| `start`, `end` | string | Echo of the range. |

Each **row** object:

| Field | Type | Meaning |
|---|---|---|
| `main_group` | string | Channel / [[Main Group]] — `GT` / `MT` / `ROI` / `E-COMMERCE` / `CSD` / … |
| `state` | string | Ship-to state (full name). |
| `person` | string | Raw invoice sales-person UDF (the page ignores this and instead maps `main_group`+`state` → assigned territory owner). |
| `product` | string | Sub-group / variety (MUSTARD, OLIVE, CANOLA, …). |
| `item_name` | string | SAP item — `"<code> — <description>"`. |
| `customer` | string | CardName / buyer. |
| `u_type` | string | `PREMIUM` / `COMMODITY` (oil only; blank for beverages). |
| `sales_qty` | number | Gross sales quantity (litres or boxes). |
| `sales_rev` | number | Gross sales revenue ₹ (taxable). |
| `cng_qty` | number | Credit-note **for Goods** quantity (product returns). |
| `cng_rev` | number | Credit-note for Goods value ₹. |
| `cns_rev` | number | Credit-note **for Services** value ₹ (claims — discounts / FOC / samples; has no quantity). |

Derived client-side per node: `Total CN = cng_rev + cns_rev`, `Net Sales = sales_rev − Total CN`. In Litres/Boxes mode only `cng_qty` counts as CN (service claims carry no quantity).

TRIMMED sample (oil, single day):
```json
{"status":"ok","company":"oil","measure":"Litres","has_type":true,
 "rows":[{"main_group":"GT","state":"DELHI","person":"DELHI GT","product":"MUSTARD",
   "item_name":"FG0000030 — MUSTARD KACHI GHANI 1 LTR 20 PCS","customer":"RAJESHWAR KISHORE MAHENDERPAL",
   "u_type":"COMMODITY","sales_qty":4000.0,"sales_rev":620920.0,
   "cng_qty":0.0,"cng_rev":0.0,"cns_rev":0.0}], "start":"2026-07-22","end":"2026-07-22"}
```

## Used by
[[sales-cn]]

## Notes
- READ-only, probed live (single day for oil, single day for beverages). Returned 27 rows for a single beverages day; oil rows confirm the `cng_*`/`cns_*` split.
- Excel export is a **separate** call to the shared `export-xlsx/` endpoint (WRITE/file — client posts the already-rendered pivot; not this endpoint). Not documented here.
- "CN for Goods" vs "Claim for Services" is the core distinction — see [[credit-note]].
