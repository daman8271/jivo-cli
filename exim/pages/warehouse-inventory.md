---
title: Warehouse Inventory
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/warehouse-inventory
section: Reports
---

# Warehouse Inventory

[[INDEX|JIVO EXIM]] › **Reports** › Warehouse Inventory

**Route:** `/stock/warehouse-inventory`  ·  **Web:** `https://exim.jivo.in/stock/warehouse-inventory`

## What this page does

SAP-synced warehouse stock in two views: raw/factory inventory from `GET /sap-sync/inventory/` (~50 Warehouse × Category rows, e.g. BH-CRUDE / CANOLA / 177,261) and finished goods from `GET /sap-sync/finished-inventory/` (~22 rows, e.g. BH-EC / BLENDED / 5,125). Each row is a warehouse code, an oil category, and the total quantity held there.

## How it helps

Answers "what is physically in each warehouse right now, per oil category" straight from SAP, without logging into SAP. Ops use it to spot empty crude positions (e.g. BH-EX CANOLA at 0) and finished-goods cover before planning dispatches or new imports.

## Backend endpoints

- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]] — Finished-goods inventory (SAP).
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]] — Raw/factory inventory (SAP).

## Key data & interactions

- Raw / Finished tab switch (inventory vs finished-inventory endpoint)
- Table columns: Warehouse (BH-CRUDE, BH-EX, BH-EC, GP-FG...), Category (CANOLA, BLENDED, MUSTARD...), Total quantity
- Filter by warehouse and category; Hide-Empty toggle for zero-Total rows
- Refresh to re-sync from SAP

## Related pages (same section)

- [[pages/dashboard|Dashboard]]
- [[pages/stock-dashboard|Stock Dashboard]]
- [[pages/director-dashboard|Director Dashboard]]
- [[pages/vehicle-report|Vehicle Report]]
- [[pages/contracts|Contracts]]
- [[pages/planning|Planning]]


Linked: [[INDEX]] · [[API-INVENTORY]]
