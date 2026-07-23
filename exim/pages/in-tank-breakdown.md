---
title: In Tank Breakdown
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/in-tank-breakdown
section: Stock
---

# In Tank Breakdown

[[INDEX|JIVO EXIM]] › **Stock** › In Tank Breakdown

**Route:** `/stock/in-tank-breakdown`  ·  **Web:** `https://exim.jivo.in/stock/in-tank-breakdown`

## What this page does

Batch-level costing for oil sitting in tanks. The user picks an item from the distinct in-tank list (`GET /tank/in-tank-items/`, ~28 item codes) and the page calls `GET /tank/item-wise-average/?item_code=` to show that item's tank_total_capacity (litres and kg), quantity_matched vs quantity_unmatched, weighted average_rate (IN_TANK) and adjusted_average (STO) in both ₹/litre and ₹/kg, plus a batch breakdown listing each contributing stock_id with party, vehicle, rate_in_litres/kg, batch_quantity, quantity_consumed and batch_total value. Item names, categories and colours come from `GET /tank/items/`.

## How it helps

This answers "what does the oil in our tanks actually cost us" - the weighted average blends multiple batches bought at different rates from different parties (e.g. CANOLA averaging ₹125.55/litre in-tank vs ₹137.97/kg STO-adjusted). Finance uses it for valuation and transfer pricing; ops uses quantity_matched vs unmatched to spot batches not yet reconciled to tank stock.

## Backend endpoints

- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]] — Distinct item codes currently in tanks.
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]] — Weighted average rate + matched qty for one tank item.
- [[endpoints/tank_items|`GET /tank/items/`]] — Tank item master (code, name, category, colour).

## Key data & interactions

- Item selector limited to codes currently in tanks (from `/tank/in-tank-items/`)
- Summary metrics per item: tank_total_capacity (L and KG), quantity_matched, quantity_unmatched, average_rate (IN_TANK) and adjusted_average (STO) in ₹/L and ₹/KG
- KG vs LITERS view of rates and quantities
- Batch breakdown table: stock_id, created_at, party, vehicle, transporter, rate_in_litres/rate_in_kg, batch_quantity, quantity_consumed, batch_total value

## Related pages (same section)

- [[pages/stock-status|Stock Status]]
- [[pages/shortage-report|Shortage Report]]
- [[pages/contractual-history|Contractual History]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-monitoring|Tank Monitoring]]
- [[pages/tank-data|Tank Data]]
- [[pages/tank-logs|Tank Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
