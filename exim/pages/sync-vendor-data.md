---
title: Sync Vendor Data
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /admin/sync-vendor-data
section: Administration
---

# Sync Vendor Data

[[INDEX|JIVO EXIM]] › **Administration** › Sync Vendor Data

**Route:** `/admin/sync-vendor-data`  ·  **Web:** `https://exim.jivo.in/admin/sync-vendor-data`

## What this page does

Shows the SAP-synced business-partner master: `GET /parties/` returns 137 parties (vendors and customers), each with `card_code` (e.g. `VENDA000102`), `card_name`, `state` (GJ, HR, ...), `country`, and `u_main_group` (EXPORT, PURCHASE OIL, ...). This is the admin check that the party list used by Stock Status and domestic contract pages matches SAP.

## How it helps

Ops users open this page after a party sync to confirm a newly created SAP vendor or customer is available in EXIM before they try to book a stock entry or domestic contract against it. A missing or misgrouped party here explains why a name does not appear in downstream dropdowns.

## Backend endpoints

- [[endpoints/parties|`GET /parties/`]] — Business partners (vendors + customers) master from SAP.

## Key data & interactions

- Party table: Card Code, Card Name, State, Country, Main Group (`u_main_group`: EXPORT, PURCHASE OIL, ...)
- Total count indicator (137 parties)
- Search/filter by card code, name, or main group
- Sync / Refresh action to re-pull parties from SAP

## Related pages (same section)

- [[pages/users|Users]]
- [[pages/sync-raw-material|Sync Raw Material]]
- [[pages/sync-finished-goods|Sync Finished Goods]]
- [[pages/sync-logs|Sync Logs]]
- [[pages/stock-updation-logs|Stock Updation Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
