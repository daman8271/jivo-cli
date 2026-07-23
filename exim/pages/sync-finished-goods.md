---
title: Sync Finished Goods
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /admin/sync-finished-goods-data
section: Administration
---

# Sync Finished Goods

[[INDEX|JIVO EXIM]] › **Administration** › Sync Finished Goods

**Route:** `/admin/sync-finished-goods-data`  ·  **Web:** `https://exim.jivo.in/admin/sync-finished-goods-data`

## What this page does

Shows the SAP-synced finished-goods item master: `GET /items/fg/` returns 331 packed SKUs, each with `item_code` (FG-prefixed, e.g. `FG0000424`), `item_name` (e.g. COLD PRESS SUNFLOWER 1 LTR 24 PCS), `category`, `u_variety` (SUNFLOWER, OLIVE, ...), `u_brand` (JIVO), pack size `sal_pack_un`, units per case `sal_factor2`, GST rate `u_tax_rate`, sub-group/location `u_sub_group`, and the `deleted` flag. This is the admin view for verifying that the FG catalog pulled from SAP is current and complete before it feeds other pages.

## How it helps

An ops/admin user opens this page after a SAP sync to confirm new or changed finished-goods SKUs (pack sizes, tax rates, varieties) landed correctly in EXIM. Catching a stale or missing FG item here prevents wrong item picks downstream in stock and contract entry.

## Backend endpoints

- [[endpoints/items_fg|`GET /items/fg/`]] — Finished-goods item master (SAP-synced).

## Key data & interactions

- Item table: Item Code, Item Name, Category, Variety (`u_variety`), Brand (`u_brand`), Pack Size (`sal_pack_un`), Units/Case (`sal_factor2`), Tax Rate % (`u_tax_rate`), Sub Group (`u_sub_group`), Deleted flag
- Total count indicator (`count`, currently 331 items)
- Text search / filter by item code, name, or variety
- Sync / Refresh action to re-pull the FG master from SAP

## Related pages (same section)

- [[pages/users|Users]]
- [[pages/sync-raw-material|Sync Raw Material]]
- [[pages/sync-vendor-data|Sync Vendor Data]]
- [[pages/sync-logs|Sync Logs]]
- [[pages/stock-updation-logs|Stock Updation Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
