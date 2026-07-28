---
endpoint: /realise/api/compare-docs/
method: POST
auth: session + X-CSRFToken (JSON body)
readonly: true
used_by: [compare-sales]
tags: [jivo, api, sales, drill-down]
---
# `POST /realise/api/compare-docs/`

## Purpose
Invoice-level **drill-down** for the [[compare-sales]] pivot. When a user clicks a single month × dimension value cell in Compare Sales, this returns the actual invoices (and their item lines) behind that number — doc number, party, litres, boxes, taxable value, and per-item rate. It answers "which invoices make up this cell?".

## Request
JSON body (`Content-Type: application/json` + `X-CSRFToken`). The page builds the body from the clicked cell's month range plus the pivot node's filter path:

| Field | Type | Meaning |
|---|---|---|
| `start_date` | `YYYY-MM-DD` | 1st of the clicked month. |
| `end_date` | `YYYY-MM-DD` | Last day of the clicked month. |
| `seg` | `""` \| `"PREMIUM"` \| `"COMMODITY"` | Type filter carried from the page's Type dropdown. |
| `group` | string? | Main Group narrowing, if that dimension is in the drill path. |
| `state` | string? | State narrowing, if in the path. |
| `person` | string? | Assigned territory owner narrowing, if in the path. |
| `product` | string? | Product / sub-group narrowing, if in the path. |
| `item` | string? | Item name narrowing, if in the path. |
| `customer` | string? | Customer narrowing, if in the path. |

Only the filter keys present in the active drill path are sent (dynamic — `for(k in filters)payload[k]=filters[k]`). The dimension keys mirror Compare Sales `DIMS`: `group`, `state`, `person`, `product`, `item`, `customer`.

## Response
HTTP 200 · `Content-Type: application/json`. Top-level keys:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"` / `"error"`. |
| `count` | number | Number of invoices returned. |
| `data` | array | One object per invoice (document header), each with nested `items`. |

Each **invoice** (`data[]`):

| Field | Type | Meaning |
|---|---|---|
| `doc_num` | string | SAP DocNum. |
| `doc_date` | `YYYY-MM-DD` | Invoice date. |
| `party` | string | Customer / CardName. |
| `state` | string | Ship-to state. |
| `litres` | number | Invoice total litres. |
| `boxes` | number | Invoice total boxes (can be fractional). |
| `taxable` | number | Invoice taxable value ₹. |
| `items` | array | Line items. |

Each **item** (`data[].items[]`):

| Field | Type | Meaning |
|---|---|---|
| `name` | string | `"<code> — <description>"`. |
| `boxes` | number | Line box qty. |
| `litres` | number | Line litres. |
| `taxable` | number | Line taxable value ₹. |
| `rate` | number | Rate per bottle/unit ₹. |

Realise ₹/L is computed client-side as `taxable / litres`.

TRIMMED sample (single day, `group=E-COMMERCE`):
```json
{"status":"ok","count":11,
 "data":[{"doc_num":"626070466","doc_date":"2026-07-22","party":"JIVO MART PVT LTD","state":"HARYANA",
   "litres":61179.0,"boxes":3086.52,"taxable":9297450.0,
   "items":[{"name":"FG0000081 — COLD PRESS SUNFLOWER 1 LTR 20 PCS",
     "boxes":2847.5,"litres":56950.0,"taxable":8542500.0,"rate":150.0}]}]}
```

## Used by
[[compare-sales]] (invoice drill modal only — the pivot itself is built from `sales-data/`, a different endpoint).

## Notes
- READ-only, probed live with a single-day range + one group filter (11 invoices). Scoped by design (one month, one cell) so payloads are naturally small.
- The main Compare Sales grid is loaded from `/realise/api/sales-data/` (not owned by this slice); `compare-docs/` is strictly the click-through detail.
