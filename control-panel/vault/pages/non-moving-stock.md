---
title: Non Moving Stock
aliases: [non-inventory]
route: /inventory/non-inventory/
type: page
endpoints: [inventory-non-inventory-data, inventory-non-inventory-drill]
tags: [jivo, control-panel, inventory]
---
# Non Moving Stock

## Purpose
Surfaces **slow-moving / dead finished-goods stock** — items that have sat in the warehouse without being billed for a long time — so ops can chase liquidation, discounts, or transfers before the stock ages out. For every in-stock FG it shows how long it's been in stock, when it was last sold, to whom, and how much value is stuck. (Route is `/inventory/non-inventory/`; sidebar label "Non Moving Stock", page title "Finished Goods — Non Moving Stock".)

## What it shows
- **Company segment** — Jivo Oil / Jivo Mart / Jivo Beverages (`schema`; default Jivo Oil).
- **"Not moved ≥ N days" threshold** — numeric input, **default 60**. Client-side filter keeping only items whose `DaysSinceMoved ≥ N`; set 0 to show everything.
- **Ageing table** — one row per FG: item, sub-group/variety/SKU, Prod Date, **Days In Stock**, Last Billed, **Days · Billed** (ageing-coloured: >180 red/hot, >90 amber/warm, else cool), a "months + days" month cell, and Qty / Ltr / Boxes / Value.
- **Search** over item / variety / customer.
- **Row drill** — expanding a row calls [[inventory-non-inventory-drill]] to break that item's stock out **by warehouse** (code, name, qty, lot production date).

## Data sources
- [[inventory-non-inventory-data]] — `GET …/api/data/?schema=`: full in-stock FG list with ageing/movement fields. The "non-moving" cut is applied client-side on `DaysSinceMoved`.
- [[inventory-non-inventory-drill]] — `GET …/api/drill/?schema=&item=[&whs=]`: per-warehouse breakdown for one item.

## Key fields & columns
- **Days In Stock** (`DaysInStock`) → age since `ProdDate` of the on-hand lot.
- **Days Since Billed** (`DaysSinceBilled`) → days since the item was last sold; drives the heat colour.
- **Days Since Moved** (`DaysSinceMoved`) → days since last movement — **the field the threshold filters on** (the definition of "non-moving").
- **Last Customer / Last Code** → who last bought it (party name + SAP card code, e.g. `CUSTA000606`). See [[customer-master]].
- **Qty / Litres / Boxes** → on-hand in each unit; **Value** → ₹ stuck in that stock.
- **Per-unit factors** (`LitrePer`, `BoxPer`, `PricePer`) → conversion + price used to derive litres/boxes/value.
- **wh** → `{warehouse: qty}` where stock sits (see [[warehouses]]).

## Notes / gotchas
- "Non-moving" is **not** a server flag — it's purely the client-side `DaysSinceMoved ≥ threshold` filter; changing the number reclassifies instantly.
- Live snapshot. `DaysSinceMoved` (last movement) can differ from `DaysSinceBilled` (last sale) if the item moved via a non-billing transaction.
- Warehouse set here is the finished-goods godowns (e.g. BH-EC / BH-FG / BH-PF / GP-FG) — a subset of the full master.

## Related
- [[stock-available]], [[production-plan]], [[daily-production]], [[warehouses]], [[customer-master]], [[segments-oils-beverages]]
