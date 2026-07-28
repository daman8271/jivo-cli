---
title: Daily Production
route: /inventory/daily-production/
type: page
endpoints: [inventory-daily-production-data]
tags: [jivo, control-panel, inventory, production]
---
# Daily Production

## Purpose
Shows **what actually got produced each day** — the standard **work-order (OWOR)** transactions — so ops can track daily output volume, planned-vs-completed, and who ran what. Where [[production-plan]] asks "can we make it?", this page reports "what did we make?". (Route `/inventory/daily-production/`; page title "Daily Production Transaction".)

## What it shows
- **Date range** — From/To driving [[inventory-daily-production-data]] (`start`/`end`).
- **KPI cards** (client-side from rows): **Work Orders** (count), **Total Litres** (completed × pack size), **Total Boxes** (completed ÷ box size), **Completed Qty** (units produced).
- **Warehouse multi-select** — built from the returned rows; **default filter `BH-PF`** (Bhakharpur Production Finished 1st Floor). See [[warehouses]].
- **Drill-by-dimension pivot** — group the table by any ordered combination of **Date › Variety › Item Name › Warehouse › User** (default order: Date › Item Name). Measures per group: Work Orders, Planned Qty, Completed Qty, Litres, Boxes.
- **Search** over item / variety / user / doc / warehouse.

## Data sources
- [[inventory-daily-production-data]] — `GET …/api/data/?start=&end=`: flat list of work-order rows for the window; all KPIs and pivoting are computed client-side.

## Key fields & columns
- **doc** → work-order document number (OWOR).
- **status** → `Planned` (not started) / `Released` / `Closed` (done).
- **planned** vs **completed** → target vs actual produced quantity.
- **litres** → completed × pack size; **boxes** → completed ÷ box size.
- **variety** → oil sub-group / line (CANOLA, PET BOTTLES…). Note bottle/PM lines (blowing PET bottles) appear alongside FG lines.
- **warehouse** → production godown the order ran in (default view BH-PF).
- **user** → SAP user who created the work order.

## Notes / gotchas
- Covers **standard work orders (OWOR) only** — not special/rework orders.
- Rows include upstream **packing-material production** (e.g. PET bottle blowing, `PM…` items) as well as finished-oil fills — filter by variety/item if you only want FGs.
- Read-only; live transactional data for the chosen dates.

## Related
- [[production-plan]], [[stock-available]], [[non-moving-stock]], [[warehouses]]
