---
endpoint: /realise/api/channel-targets/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/channel-targets/`

## Purpose
Returns the monthly **target litres per sales channel** (main group). Drives the "Target Ltr" figure on each channel card of the [[sales-dashboard]] Slide-2 channel view.

## Request
Query params:
- `month` (int 1–12), `year` (int) — target period.

## Response
HTTP 200. Keys: `status`, `month`, `year`, `data`. `data` is an object mapping channel code → target litres (float).

Trimmed sample:
```json
{"status":"ok","month":7,"year":2026,
 "data":{"GT":685000.0,"ROI":256000.0,"MT":215000.0,"HORECA":40000.0,"CSD":15000.0,"REST":30000.0,"ECOM":1300000.0}}
```

## Used by
[[sales-dashboard]] (Slide-2 channel card targets).

## Notes
GET read. Channel codes: [[GT]] (General Trade), [[MT]] (Modern Trade), [[ROI]] (Rest of India), [[ECOM]] (E-Commerce), HORECA, CSD (canteen stores dept), REST. Compare "Done"/"OIH" actuals from [[sales-data]] / [[order-in-hand-rows]] against these. Concept: [[TGT]].
