---
title: Stock Available
route: /inventory/stock-available/
type: page
endpoints: [inventory-stock-available-data]
tags: [jivo, control-panel, inventory]
---
# Stock Available

## Purpose
Gives JIVO ops a **live view of finished-goods on-hand stock** across the finished-goods godowns, so they can see at a glance how many litres/units of each product (and each SKU) are sitting where. Stock is computed **In − Out** across the five finished warehouses **GP-FG / BH-FG / BH-PF / BH-EC / BH-FU** (see [[warehouses]]). It is the "how much do we have?" companion to [[production-plan]] ("can we make more?") and [[non-moving-stock]] ("what's not selling?").

## What it shows
- **Company segment** — **Jivo Oil** / **Jivo Mart** / **Jivo Beverages** (sets `schema`; default Jivo Oil). Switching refetches [[inventory-stock-available-data]].
- **Summary KPI band** — **Total** litres/boxes + one card per major type. Oils show **Total / Premium / Commodity**; beverages show **Total / Water / Drinks** (top two metric types). See [[segments-oils-beverages]].
- **Type segment** — built from the data (Premium/Commodity for oils; DRINKS/WATER/… for beverages); client-side filter of the cards.
- **Product cards grid** — one card per sub-group, colour-coded per product, showing on-hand **litres** (oils) or **boxes** (beverages) and SKU count. Click a card to open its drill table.
- **Drill table** — per-SKU rows with a column **per warehouse** (GP-FG / BH-FG / BH-PF / BH-EC / BH-FU) plus a **Grand Total**, and a sticky total row. A **SKU multi-select** filters which pack sizes show.
- **Export Excel** — separate route `/inventory/stock-available/export/?schema=` ("Inventory Audit Report" pivot, file download — WRITE/file side, not probed).

## Data sources
- [[inventory-stock-available-data]] — `GET …/api/data/?schema=`: the whole page (warehouses list, product summaries, per-SKU × per-warehouse rows). One call; all type/SKU filtering is client-side.

## Key fields & columns
- **Type** → PREMIUM / COMMODITY for oils (beverage types differ). Expands via [[segments-oils-beverages]].
- **Sub-group** → product family (OLIVE, CANOLA, MUSTARD, SOYABEAN…).
- **Qty** → on-hand physical units (bottles/jars/boxes).
- **Litres** → on-hand converted to litres (pack size × qty); the headline oil metric.
- **SKU count** → distinct pack sizes with stock in that sub-group.
- **Per-warehouse columns** → on-hand units in each of GP-FG / BH-FG / BH-PF / BH-EC / BH-FU. See [[warehouses]] for what each godown is.
- **Grand Total** → sum across the five finished warehouses.

## Notes / gotchas
- **Live snapshot**, no history — reflects current SAP on-hand, not a dated report.
- Only the **five finished-goods** warehouses are summed; raw/packing/transit/job-work godowns are excluded from this page (they appear on [[production-plan]] component locations).
- `BH-FU` shows here but is **not** in the production warehouse master returned by [[inventory-production-warehouses]].
- Beverages are measured in **boxes**, oils in **litres** — the KPI/card unit switches with the company segment.

## Related
- [[non-moving-stock]], [[production-plan]], [[daily-production]], [[oih-vs-stock]], [[warehouses]], [[segments-oils-beverages]], [[OIH]]
