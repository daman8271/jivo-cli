---
endpoint: /realise/api/beverages-docs/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard, beverages]
---
# `GET /realise/api/beverages-docs/`

## Purpose
Returns the underlying **documents** (invoices / sales orders) behind a beverages node in the [[sales-dashboard]] [[BEVERAGES]] view — lazily fetched when a user expands a node row (`bevToggleDocs`).

## Request
Query params (built in `bevToggleDocs`):
- `metric` (str, required) — which measure the node represents, e.g. `quantity` (also `boxes`/`oih` per node metric).
- `start`, `end` (str, `YYYY-MM-DD`, required) — the beverages range (`bevRangeStart`/`bevRangeEnd`).
- `f_<key>` (str, optional, repeatable) — node path filters, one per drill level (e.g. `f_customer`, `f_variety`).
- `f_brand` (str, optional) — active brand filter.
- `f_ym` (str, optional) — active month filter (`YYYY-MM`).

## Response
HTTP 200. Keys: `status`, `metric` (echoed), `count`, `data`. `data` is an array of documents: `{doc_num, doc_date, customer, quantity, boxes}`.

Trimmed sample (`metric=quantity`):
```json
{"status":"ok","metric":"quantity","count":20,
 "data":[{"doc_num":"626078243","doc_date":"2026-07-22","customer":"GURU RAMDAS DISTRIBUTORS","quantity":12000.0,"boxes":500.0}]}
```

## Used by
[[sales-dashboard]] (BEVERAGES node → document list).

## Notes
GET read. The `f_` prefix convention encodes each node filter as a separate query param. Oils-side equivalent is [[channel-detail-docs]]. Concept: [[BEVERAGES]].
