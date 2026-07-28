---
endpoint: /realise/api/channel-detail-docs/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/channel-detail-docs/`

## Purpose
Returns the underlying **documents** behind a Slide-2 channel card / cell on the [[sales-dashboard]] — either invoices ("Done") or open sales orders ("[[OIH]]") — with per-line items and per-warehouse stock. Opened in the doc-detail modal when a user clicks a channel figure.

## Request
Query params (`URLSearchParams`):
- `channel` (str) — channel/main-group code, e.g. `GT`, `MT`, `ECOM` (empty = all).
- `metric` (str) — `done` (invoices) or `oih` (open sales orders); default `done`.
- `seg` (str) — segment scope, e.g. `OILS`.
- `start`, `end` (str, `YYYY-MM-DD`) — from Slide-2 `sc2From`/`sc2To`.
- plus any active dimension filters: `group`, `state`, `person`, `product`, `item`, `customer` (each set when present).

## Response
HTTP 200. Keys: `status`, `metric` (echoed), `count`, `warehouses`, `data`.
- `warehouses` — column order for each item's `stock` triple, e.g. `["GP-FG","BH-EC","BH-PF"]`.
- `data` — document rows: `{doc_num, doc_date, party, state, city, litres, balance, items:[{name, stock:[..per warehouse..], litres}]}`. For `done`, `doc_num` is an invoice no & `doc_date` its date; for `oih`, an SO no & SO date.

Trimmed sample (`metric=oih, channel=GT`):
```json
{"status":"ok","metric":"oih","count":50,"warehouses":["GP-FG","BH-EC","BH-PF"],
 "data":[{"doc_num":"1726066559","doc_date":"2026-06-05","party":"SHIVAY EDIBLES PRIVATE LIMITED","state":"DELHI","city":"EAST DELHI","litres":180000.0,"balance":4939998.0,
   "items":[{"name":"FG0000030 — MUSTARD KACHI GHANI 1 LTR 20 PCS","stock":[0,0,900.0],"litres":180000.0}]}]}
```

## Used by
[[sales-dashboard]] (channel card → doc-detail modal).

## Notes
GET read. `stock` array aligns positionally to `warehouses`. **Gotcha:** a narrow channel+segment+single-day combo can return `count:0` (e.g. GT/OILS `done` for one day was empty) while `metric=oih` (open orders, not date-bound) returns rows. `balance` = document ₹ balance. Beverages equivalent is [[beverages-docs]]. Concepts: [[GT]], [[MT]], [[ECOM]], [[OIH]], [[DONE]].
