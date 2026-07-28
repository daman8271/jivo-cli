---
endpoint: /realise/api/order-in-hand-rows/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/order-in-hand-rows/`

## Purpose
Returns **[[OIH]]** as individual open-order rows (open litres per item/customer) for the Slide-2 channel detail on the [[sales-dashboard]]. Cached client-side as `detailOihRowsCache`.

## Request
Query params (built by `sc2DateQS()` from the Slide-2 date pickers `sc2From`/`sc2To`):
- `start` (str, `YYYY-MM-DD`, optional) — range start.
- `end` (str, `YYYY-MM-DD`, optional) — range end.

## Response
HTTP 200. Keys: `status`, `data`. `data` is an array of open-order rows: `{main_group, state, sales_person, card_name, u_type, u_sub_group, item_name, sku, open_qty}`.

Trimmed sample:
```json
{"status":"ok","data":[
 {"main_group":"E-COMMERCE","state":"KARNATAKA","sales_person":"PRABHU SIR","card_name":"INNOVATIVE RETAIL CONCEPTS PVT LTD","u_type":"PREMIUM","u_sub_group":"BLENDED","item_name":"BB ROYAL CANOLA OIL 1 LTR 20 PCS","sku":"1 LTR","open_qty":520.0}]}
```

## Used by
[[sales-dashboard]] (Slide-2 OIH detail rows).

## Notes
GET read. `open_qty` = uninvoiced litres still open on the SO. Commodity-oil counterpart is [[commodity-oih-rows]]; ₹-value/line detail is [[oih-breakdown]]; per-person totals in [[order-in-hand]]. Concept: [[OIH]], [[Main Group]].
