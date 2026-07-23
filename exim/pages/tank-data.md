---
title: Tank Data
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/tank-data
section: Stock
---

# Tank Data

[[INDEX|JIVO EXIM]] › **Stock** › Tank Data

**Route:** `/stock/tank-data`  ·  **Web:** `https://exim.jivo.in/stock/tank-data`

## What this page does

The tank register: `GET /tank/` lists all 32 tanks with tank_code (e.g. TNK005), assigned item_code, tank_capacity, current_capacity, tank_type, is_active and updated_at, with item names/colours resolved via `GET /tank/items/` and totals from `GET /tank/tank-summary/`. This is where tanks are administered: create a tank (`POST /tank/`), edit it (`PATCH /tank/{tank_code}/`), or adjust its capacity (`PATCH /tank/update-capacity/{id}/`).

## How it helps

Keeps the physical tank farm and the system in sync: when a tank is added, re-assigned to a different oil, or re-measured, this page is where the change is made, so utilisation math on Tank Monitoring stays honest. The capacity-vs-current columns show exactly how much room each tank has before the next inward load.

## Backend endpoints

- [[endpoints/tank|`GET /tank/`]] — Create a tank.
- [[endpoints/tank_items|`GET /tank/items/`]] — Tank item master (code, name, category, colour).
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]] — Tank totals (capacity, current stock, utilisation).

## Key data & interactions

- Summary strip from tank-summary: total capacity, current stock, utilisation %, tank count, item count
- Tank table: tank_code, item_code (with item name/colour), tank_capacity, current_capacity, tank_type, is_active, updated_at
- Add-tank form (POST /tank/), per-row edit (PATCH /tank/{tank_code}/) and capacity update (PATCH /tank/update-capacity/{id}/)
- Filter by item and active status

## Related pages (same section)

- [[pages/stock-status|Stock Status]]
- [[pages/shortage-report|Shortage Report]]
- [[pages/contractual-history|Contractual History]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-monitoring|Tank Monitoring]]
- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/tank-logs|Tank Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
