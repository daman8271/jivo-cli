---
endpoint: /realise/api/sales-flow/
method: POST
auth: session + X-CSRFToken
readonly: true
used_by: [sales-flow]
tags: [jivo, api, sales, flow-dispatch]
---
# `POST /realise/api/sales-flow/`

## Purpose
Returns one day-range's worth of **sales document chains** — for each customer, the linked Sales Quotation → Sales Order → Invoice, with invoiced volume, open/closed status of each document, and the source (OMS software vs SAP user) that created each. Backs the [[sales-flow]] page.

## Request
JSON body (`Content-Type: application/json` + `X-CSRFToken` from the `csrftoken` cookie / page `<meta name=csrf-token>`):

| Field | Type | Meaning |
|---|---|---|
| `start_date` | string `YYYY-MM-DD` | Range start (page defaults both to *yesterday*). |
| `end_date` | string `YYYY-MM-DD` | Range end. |
| `company` | string | `"oil"` or `"beverages"` — selects the SAP company DB and the volume unit. Defaults to oil. |

Example: `{"start_date":"2026-07-22","end_date":"2026-07-22","company":"oil"}`

## Response
HTTP 200. Top-level keys:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"` (or `"error"` with an `error` message). |
| `company` | string | Echo of requested company. |
| `measure` | string | `"Litres"` for oil, `"Boxes"` for beverages — drives the qty column/KPI label. |
| `start` / `end` | string | Echo of the requested date range. |
| `rows` | array | One object per document chain (see below). |

Each `rows[]` object:
- `party` (string) — customer name · `card_code` (string) — SAP business-partner code.
- `date` (string `YYYY-MM-DD`).
- `quotation_no` / `order_no` / `invoice_no` (string) — SAP doc numbers; empty string when that step was skipped.
- `qty` (number) — invoiced volume in `measure` units.
- `quotation_src` / `order_src` / `invoice_src` — `null`, or `{oms:bool, label:string, user:string}` (OMS/B1i vs the SAP user who keyed it).
- `quotation_open` / `order_open` / `invoice_open` (bool) — whether that document still has open lines.

TRIMMED 1-row sample (oil, 2026-07-22):
```json
{
  "status": "ok", "company": "oil", "measure": "Litres",
  "start": "2026-07-22", "end": "2026-07-22",
  "rows": [{
    "party": "JIVO MART PVT LTD", "card_code": "CUSTA000606", "date": "2026-07-22",
    "quotation_no": "", "order_no": "1726076736", "invoice_no": "626070469",
    "qty": 32239.0,
    "quotation_src": null,
    "order_src": {"oms": false, "label": "MANSI", "user": "MANSI"},
    "invoice_src": {"oms": false, "label": "SUMIT", "user": "SUMIT"},
    "quotation_open": false, "order_open": true, "invoice_open": true
  }]
}
```
(oil day: 17 rows; beverages same day: 21 rows, `measure":"Boxes"`.)

## Used by
[[sales-flow]]

## Notes
- READ endpoint — safe. Probed live with a single day (17 rows) per read-only discipline; do not pull months.
- An empty `order_no`/`quotation_no` is meaningful (direct order / direct invoice), not a data gap.
- Open documents (`order_open:true`) are drillable to line level via [[sales-flow-open-items]].
