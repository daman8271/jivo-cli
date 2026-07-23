---
title: Tank Items
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/tank-items
section: Stock
---

# Tank Items

[[INDEX|JIVO EXIM]] › **Stock** › Tank Items

**Route:** `/stock/tank-items`  ·  **Web:** `https://exim.jivo.in/stock/tank-items`

## What this page does

The master list of oil items that can live in tanks, from `GET /tank/items/`: 51 items in the sample, each with tank_item_code (e.g. RMSESMT), tank_item_name (SESAME TOASTED), category (SESAME), an is_active flag, a display color hex used across tank charts, and created_at/created_by. New items are added via `POST /tank/item/` and colours changed via `PATCH /tank/item/update-color/{id}/`.

## How it helps

This is the reference data behind every tank view: an item must exist here before a tank can be assigned to it or stock rows can reference it. The per-item colour keeps Tank Monitoring and In Tank Breakdown visuals consistent, so ops recognises an oil at a glance.

## Backend endpoints

- [[endpoints/tank_items|`GET /tank/items/`]] — Tank item master (code, name, category, colour).

## Key data & interactions

- Item table: tank_item_code, tank_item_name, category, colour swatch, is_active, created_at, created_by
- Search/filter by code, name, or category (e.g. all SESAME items)
- Add-item form (POST /tank/item/) and a colour picker per row (PATCH /tank/item/update-color/{id}/)

## Related pages (same section)

- [[pages/stock-status|Stock Status]]
- [[pages/shortage-report|Shortage Report]]
- [[pages/contractual-history|Contractual History]]
- [[pages/tank-monitoring|Tank Monitoring]]
- [[pages/tank-data|Tank Data]]
- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/tank-logs|Tank Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
