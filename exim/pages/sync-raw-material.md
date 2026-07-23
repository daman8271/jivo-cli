---
title: Sync Raw Material
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /admin/sync-raw-material-data
section: Administration
---

# Sync Raw Material

[[INDEX|JIVO EXIM]] › **Administration** › Sync Raw Material

**Route:** `/admin/sync-raw-material-data`  ·  **Web:** `https://exim.jivo.in/admin/sync-raw-material-data`

## What this page does

Shows the SAP-synced raw-material item master: `GET /items/rm/` returns 23 loose-oil RMs (e.g. `RM0000001` LOOSE REFINED OLIVE OIL) with `u_variety`, `u_sub_group`, `rate`, and running totals per item (`total_in_qty`, `total_out_qty`, on-hand `total_qty` in KG, `total_trans_value`). `GET /items/rm/summary/` supplies the headline aggregates (total_count 23, total_qty ~610,957 KG, avg_rate ₹350.74, total_trans_value ~₹9.39 Cr) and `GET /items/rm/varieties/` the 13 distinct varieties (COLD PRESS, CRUDE, ...) used as a filter.

## How it helps

Ops and finance users open this page to check that RM codes, rates, and in/out quantity totals from SAP match reality before booking domestic contracts or stock movements against them. The summary KPIs give a quick read on total RM holding and value without opening SAP.

## Backend endpoints

- [[endpoints/items_rm|`GET /items/rm/`]] — Raw-material item master (SAP-synced).
- [[endpoints/items_rm_summary|`GET /items/rm/summary/`]] — Aggregate summary of raw-material items (counts, qty, value).
- [[endpoints/items_rm_varieties|`GET /items/rm/varieties/`]] — Distinct raw-material varieties.

## Key data & interactions

- KPI cards from `/items/rm/summary/`: Total Items (23), Total Qty (KG), Avg Rate (₹/KG), Total Trans Value
- Item table: RM Code, Item Name, Variety (`u_variety`), Sub Group (e.g. OLIVE, CANOLA), Rate, Total In Qty, Total Out Qty, On-hand Qty (`total_qty`), Trans Value, Tax Rate, Deleted flag
- Variety filter dropdown fed by `/items/rm/varieties/` (13 values)
- Sync / Refresh action to re-pull the RM master from SAP

## Related pages (same section)

- [[pages/users|Users]]
- [[pages/sync-finished-goods|Sync Finished Goods]]
- [[pages/sync-vendor-data|Sync Vendor Data]]
- [[pages/sync-logs|Sync Logs]]
- [[pages/stock-updation-logs|Stock Updation Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
