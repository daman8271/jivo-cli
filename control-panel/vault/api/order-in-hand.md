---
endpoint: /realise/api/order-in-hand/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/order-in-hand/`

## Purpose
Returns total **[[OIH]]** value (open, uninvoiced sales-order amount) summarised **per salesperson**. Feeds the per-owner OIH KPI on the [[sales-dashboard]].

## Request
No query params.

## Response
HTTP 200. Keys: `status`, `data`. `data` is an object mapping salesperson name → OIH amount (float; ₹ or litres per the card context).

Trimmed sample:
```json
{"status":"ok","data":{"PRABHU SIR":100630.0,"SUNNY JI":198526.89,"RAMINDER JI":166738.0058,"PRESHIT":10241.0,"TARUN":0.0}}
```

## Used by
[[sales-dashboard]].

## Notes
GET read. Person-level rollup of the same open-order book detailed line-by-line in [[oih-breakdown]] and as open-qty rows in [[order-in-hand-rows]]. Concept: [[OIH]].
