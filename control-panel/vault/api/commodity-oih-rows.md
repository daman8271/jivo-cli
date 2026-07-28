---
endpoint: /realise/api/commodity-oih-rows/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/commodity-oih-rows/`

## Purpose
Returns **[[OIH]]** open-order rows filtered to **commodity** oils (`u_type=COMMODITY`) — open litres per item/customer — for the commodity view on the [[sales-dashboard]]. Cached client-side as `commodityOihRows`.

## Request
Query params (built by `sc2DateQS()` from `sc2From`/`sc2To`):
- `start` (str, `YYYY-MM-DD`, optional).
- `end` (str, `YYYY-MM-DD`, optional).

## Response
HTTP 200. Keys: `status`, `data`. `data` is an array: `{u_type, u_main_group, u_sub_group, state, card_name, item_name, open_qty}`.

Trimmed sample:
```json
{"status":"ok","data":[
 {"u_type":"COMMODITY","u_main_group":"GT","u_sub_group":"MUSTARD","state":"PUNJAB","card_name":"DWARKA DASS NARINDER KUMAR","item_name":"MUSTARD PAKKI GHANI 2 LTR 10 PCS","open_qty":1600.0}]}
```

## Used by
[[sales-dashboard]] (commodity OIH view).

## Notes
GET read. Commodity-scoped sibling of [[order-in-hand-rows]] (note the slightly different key `u_main_group` vs `main_group`). Concept: [[OIH]], [[COMMODITY|COMMODITY vs PREMIUM]].
