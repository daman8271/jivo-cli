---
endpoint: /inventory/daily-production/api/data/
method: GET
auth: session + XHR header (X-Requested-With)
readonly: true
used_by: [daily-production]
tags: [jivo, api, inventory, production]
---
# `GET /inventory/daily-production/api/data/`

## Purpose
Returns **standard work-order (OWOR) production transactions** for a date range — one row per work order — with planned vs completed quantities, converted litres/boxes, the producing warehouse, status, and who created it. Powers the [[daily-production]] page, whose KPIs and multi-dimension pivot (Date › Variety › Item › Warehouse › User) are all built client-side from this flat row list.

## Request
| Param | Type | Meaning |
|---|---|---|
| `start` | `YYYY-MM-DD` | Range start (inclusive). |
| `end` | `YYYY-MM-DD` | Range end (inclusive). |

Built as `?start=<sd>&end=<ed>`. Sample below uses a single day to keep the pull small.

## Response
HTTP 200 · `application/json`:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"` (or `error` + `error`). |
| `rows` | object[] | One row per work order. |
| `warehouses` | string[] | Distinct production warehouses in the result (drive the warehouse filter). |
| `start` / `end` | date | Echo of the range. |

`rows[]` row:

| Field | Type | Meaning |
|---|---|---|
| `doc` | string | Work-order document number (OWOR). |
| `date` | date | Production day. |
| `item_code` / `item_name` | string | Item being produced (may be a PM bottle line or an FG). |
| `variety` | string | Oil sub-group / variety (CANOLA, PET BOTTLES…). |
| `warehouse` | string | Production godown (default page filter = `BH-PF`). See [[warehouses]]. |
| `status` | string | Work-order status — `Planned`, `Released`, `Closed`. |
| `planned` | number | Planned quantity. |
| `completed` | number | Completed (produced) quantity. |
| `litres` | number | Completed × pack size (litres). |
| `boxes` | number | Completed ÷ box size (boxes). |
| `user` | string | SAP user who created the work order. |

Trimmed sample (`start=end=2026-07-22`):
```json
{"status":"ok","start":"2026-07-22","end":"2026-07-22",
 "rows":[
   {"doc":"726202786","date":"2026-07-22","item_code":"PM0000121",
    "item_name":"PM0000121 — PET BOTTLE 1 LTR 52 GMS POMACE","variety":"PET BOTTLES",
    "warehouse":"BH-BS","status":"Closed","planned":9084.0,"completed":9084.0,
    "litres":9084.0,"boxes":9084.0,"user":"SHAHRUKH"},
   {"doc":"726202783","date":"2026-07-22","item_code":"FG0000134",
    "item_name":"FG0000134 — SANO CANOLA OIL 1 LTR 20 PCS","variety":"CANOLA",
    "warehouse":"BH-PF","status":"Planned","planned":17.0,"completed":0.0,
    "litres":0.0,"boxes":0.0,"user":"Gautam CHanana"}]}
```

## Used by
- [[daily-production]] — KPI cards (Work Orders, Total Litres, Total Boxes, Completed Qty) + drill-by-dimension table.

## Notes
- Read-only. Covers **standard work orders** only (OWOR). Rows are raw transactions; all aggregation/grouping is client-side.
