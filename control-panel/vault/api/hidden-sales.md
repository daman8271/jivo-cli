---
endpoint: /realise/api/hidden-sales/
method: POST
auth: session + X-CSRFToken (JSON body)
readonly: true
used_by: [hidden-sales]
tags: [jivo, api, sales, hidden-sales]
---
# `POST /realise/api/hidden-sales/`

## Purpose
Returns line-level **hidden** sales-invoice rows — invoices flagged `U_ARNO = 'H'` in SAP — over a date range, so the [[hidden-sales]] page can pivot them month-wise. These are real sales excluded from the dashboard's headline "Done" figure, so this report surfaces what's being held back / not counted. Oil company only.

## Request
JSON body (`Content-Type: application/json` + `X-CSRFToken`):

| Field | Type | Meaning |
|---|---|---|
| `start_date` | `YYYY-MM-DD` | Range start (inclusive). |
| `end_date` | `YYYY-MM-DD` | Range end (inclusive). |

That's all the page sends. The "Last (months)" input just computes `start_date`/`end_date` client-side before the call. Type, State, Main Group, Search, Metric and Drill-By are all applied **client-side** to the returned rows.

## Response
HTTP 200 · `Content-Type: application/json`. Top-level keys:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"` or `"error"`. |
| `rows` | array | One row per hidden invoice line. Empty `[]` when nothing is hidden in the window. |
| `start`, `end` | string | Echo of the range. |

Each **row** object:

| Field | Type | Meaning |
|---|---|---|
| `doc` | string | Invoice document number (SAP DocNum). |
| `status` | string | `Open` / `Closed`. |
| `date` | `YYYY-MM-DD` | Invoice date. Page derives `ym` (YYYY-MM) & month label from this for the month-wise pivot. |
| `card_code` | string | SAP customer code (used for distinct-customer KPI). |
| `customer` | string | CardName / buyer. |
| `item_code` | string | SAP item code. |
| `item_name` | string | `"<code> — <description>"`. |
| `cost_center` | string | OcrCode — variety / cost centre (CANOLA, MUSTARD, …). |
| `state` | string | Ship-to state. |
| `main_group` | string | Channel / [[Main Group]]. |
| `u_type` | string | `PREMIUM` / `COMMODITY`. |
| `qty` | number | Invoice-line quantity (boxes/pieces). |
| `litres` | number | Litres (qty × pack size). |
| `value` | number | Line taxable value ₹. |

Client-side metrics per node: Value ₹, Litres, Quantity, and **Realise ₹/L** (`value/litres`).

TRIMMED sample (June, schema):
```json
{"status":"ok",
 "rows":[{"doc":"626060394","status":"Open","date":"2026-06-18","card_code":"CUSTA000370",
   "customer":"SRI VENKATESH AROMAS","item_code":"FG0000015","item_name":"FG0000015 — REFINED OIL 15 LTR",
   "cost_center":"CANOLA","state":"DELHI","main_group":"GT","u_type":"PREMIUM",
   "qty":150.0,"litres":2250.0,"value":382141.5}],
 "start":"2026-06-01","end":"2026-06-30"}
```

## Used by
[[hidden-sales]]

## Notes
- READ-only, probed live. A single recent day returned `rows: []` (nothing hidden that day); a full month returned 27 rows and confirmed the schema above.
- Excel export goes through the shared `export-xlsx/` endpoint (separate; not this one).
- The "hidden" flag is `U_ARNO = 'H'` on the SAP invoice header — see [[hidden-sales]] for the ops meaning.
