---
endpoint: /realise/api/oih-breakdown/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/oih-breakdown/`

## Purpose
Line-level breakdown of the current **[[OIH]]** (Order In Hand — open sales orders not yet invoiced), one row per open SO line, split into premium vs commodity value and pieces. Backs the OIH drill/detail on the [[sales-dashboard]].

## Request
No query params (returns the full current open-order book).

## Response
HTTP 200. Keys: `status`, `rows`. `rows` is an array of open-order lines: `{main_group, state, sub_group, packtype, item, customer, so_no, sales_person, sku, premium, commodity, premium_pcs, commodity_pcs}` where `premium`/`commodity` are ₹/value and `*_pcs` are piece counts split by tier.

Trimmed sample:
```json
{"status":"ok","rows":[
 {"main_group":"E-COMMERCE","state":"WEST BENGAL","sub_group":"BLENDED","packtype":"CONSUMER PACK","item":"FG0000183 — BB ROYAL CANOLA OIL 1 LTR 20 PCS","customer":"INNOVATIVE RETAIL CONCEPTS PVT LTD","so_no":"1726056884","sales_person":"PRABHU SIR","sku":"1 LTR","premium":140.0,"commodity":0.0,"premium_pcs":140.0,"commodity_pcs":0.0}]}
```

## Used by
[[sales-dashboard]] (OIH line detail).

## Notes
GET read. Aggregate/summary counterparts: [[order-in-hand]] (₹ per person), [[order-in-hand-rows]] & [[commodity-oih-rows]] (open-qty rows). `premium`/`commodity` split maps to `u_type` PREMIUM vs COMMODITY. Concept: [[OIH]], [[Main Group]].
