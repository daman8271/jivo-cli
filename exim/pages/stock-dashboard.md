---
title: Stock Dashboard
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock-dashboard
section: Reports
---

# Stock Dashboard

[[INDEX|JIVO EXIM]] › **Reports** › Stock Dashboard

**Route:** `/stock-dashboard`  ·  **Web:** `https://exim.jivo.in/stock-dashboard`

## What this page does

Stock matrix built from `GET /stock-status/stock-dashboard/` (supports a `rounding` param): one row per RM item with an outside_factory quantity plus a status_data cell for every status-vendor pair (e.g. `ON_THE_WAY__AWL AGRI BUSINESS LIMITED`), with the status_vendors map defining which vendor columns appear under each lifecycle status. Alongside it, `GET /tank/item-wise-summary/` shows in-tank stock per item: quantity_in_liters vs total_capacity, tank_count, and the tank numbers (TNK006, TNK015, ...) holding each oil.

## How it helps

The working view for stock ops: it shows, per item, exactly how much oil sits at each pipeline stage with which vendor, and how full each tank is. Used to decide what to unload next, which vendor lot to chase, and whether tank capacity allows another arrival.

## Backend endpoints

- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]] — Multi-dimensional stock dashboard (in/outside factory, by status/vendor).
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]] — Per-item tank summary (qty, capacity, tank list).

## Key data & interactions

- Item × (status × vendor) grid: rows are RM items (item_code, item_name), column groups per status (IN_CONTRACT, ON_THE_SEA, ON_THE_WAY, UNDER_LOADING, AT_REFINERY, COMPLETED) split by vendor, plus an outside_factory column
- Summary KPIs: outside_factory_total, active_items
- `rounding` toggle for rounded vs exact quantities; By-Vendor and Hide-Empty column toggles; KG / MTS / LITERS unit toggle
- Tank panel per item: color swatch, quantity_in_liters vs total_capacity, tank_count and tank_numbers; total in-tank quantity header
- Row ordering persisted via dashboard_id (dashboard-order endpoint); Refresh

## Related pages (same section)

- [[pages/dashboard|Dashboard]]
- [[pages/director-dashboard|Director Dashboard]]
- [[pages/warehouse-inventory|Warehouse Inventory]]
- [[pages/vehicle-report|Vehicle Report]]
- [[pages/contracts|Contracts]]
- [[pages/planning|Planning]]


Linked: [[INDEX]] · [[API-INVENTORY]]
