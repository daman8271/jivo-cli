---
title: Tank Monitoring
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/tank-monitoring
section: Stock
---

# Tank Monitoring

[[INDEX|JIVO EXIM]] › **Stock** › Tank Monitoring

**Route:** `/stock/tank-monitoring`  ·  **Web:** `https://exim.jivo.in/stock/tank-monitoring`

## What this page does

The live tank-farm overview. `GET /tank/tank-summary/` gives the headline numbers (total capacity 13.5 lakh L, current stock, utilisation %, 32 tanks, 16 items in the sample); `GET /tank/item-wise-summary/` breaks stock down per item with quantity_in_liters, total_capacity, tank_count and the tank_numbers holding it, each rendered in the item's colour from `GET /tank/items/`; `GET /tank/` lists every tank with tank_capacity vs current_capacity. Clicking an item pulls its weighted average cost via `GET /tank/item-wise-average/?item_code=`.

## How it helps

Answers "how full is the refinery, and of what" in one screen: at ~66% utilisation, ops can see which items are near capacity, which tanks have headroom before the next vessel or tanker arrives, and the current average rate of what's stored. Directors use utilisation and per-item spread to time purchases and dispatches.

## Backend endpoints

- [[endpoints/tank|`GET /tank/`]] — Create a tank.
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]] — Weighted average rate + matched qty for one tank item.
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]] — Per-item tank summary (qty, capacity, tank list).
- [[endpoints/tank_items|`GET /tank/items/`]] — Tank item master (code, name, category, colour).
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]] — Tank totals (capacity, current stock, utilisation).

## Key data & interactions

- KPI cards: total tank capacity, current stock, utilisation rate %, tank count, item count
- Per-item tiles/chart (colour-coded): item code/name, quantity_in_liters vs total_capacity, tank_count, tank_numbers list
- Tank-level view: tank_code, item_code, tank_capacity, current_capacity, tank_type, is_active
- Item drill-down showing weighted average_rate (IN_TANK) and adjusted_average (STO) in ₹/L and ₹/KG

## Related pages (same section)

- [[pages/stock-status|Stock Status]]
- [[pages/shortage-report|Shortage Report]]
- [[pages/contractual-history|Contractual History]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-data|Tank Data]]
- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/tank-logs|Tank Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
