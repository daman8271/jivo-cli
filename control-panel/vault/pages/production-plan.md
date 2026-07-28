---
title: Production Plan
aliases: [production]
route: /inventory/production/
type: page
endpoints: [inventory-production-fg-list, inventory-production-warehouses, inventory-production-feasibility, inventory-production-plan]
tags: [jivo, control-panel, inventory, production]
---
# Production Plan

## Purpose
Lets ops answer **"can we produce this, and how much?"** before scheduling a run. Pick a finished good (or a basket of them) and a set of stock warehouses; the page explodes each FG's **Bill of Materials**, checks raw-material (RM) and packing-material (PM) sufficiency, and reports whether the plan is feasible plus the **maximum producible quantity** and which components fall short. (Route `/inventory/production/`; page title "Production Feasibility".)

## What it shows
- **Mode tabs** — **📦 Single item** (one FG + qty) vs **📋 Production plan (multiple)** (a basket of FG rows, quantities aggregated).
- **🏬 "Stock from" warehouse selector** — multi-select (or **ALL**) built from [[inventory-production-warehouses]]; defines which godowns' stock counts as *available*. Passed as the `warehouses` param.
- **FG picker** — searchable dropdown of manufacturable FGs from [[inventory-production-fg-list]].
- **KPIs** — **Feasible? (Yes ✅ / No ❌)**, **Max FG** (most producible), **Short components** count.
- **Component table** — per RM/PM: kind, UOM, per-FG usage, required, on-hand, **Available** (in the selected warehouses), **Balance**, **Max FG**, and a **Warehouses** cell showing where the stock sits. Red rows = short in the selection; a **↪ transferable** tag = short here but enough exists elsewhere; blue pill = BOM warehouse.

## Data sources
- [[inventory-production-fg-list]] — `GET …/api/fg-list/`: manufacturable FG catalogue (picker).
- [[inventory-production-warehouses]] — `GET …/api/warehouses/`: warehouse master ("Stock from" selector), loaded lazily.
- [[inventory-production-feasibility]] — `GET …/api/feasibility/?fg_code=&qty=&warehouses=`: single-item BOM sufficiency.
- [[inventory-production-plan]] — `GET …/api/plan/?items=<JSON>&warehouses=`: multi-item aggregated sufficiency (shared components pooled).

## Key fields & columns
- **RM / PM** → raw material vs packing material (bottles, caps, labels, tape).
- **per_fg** → component consumed per 1 FG; **required** = per_fg × planned qty.
- **Available** → stock across the **selected** warehouses (drives Balance & Max FG); **all_wh** = across every warehouse.
- **Balance** → available − required (negative = short).
- **Max FG** → most FGs producible, limited by the scarcest component; can be **negative** when a component is already oversold in SAP.
- **feasible / short / elsewhere** → whole-plan feasibility, per-component shortfall, and whether a shortfall is coverable by transfer from another warehouse.
- **fg_onhand** → FGs already in stock (from [[stock-available]] context).

## Notes / gotchas
- Pure **read-only** computation — nothing is produced or consumed; no work order is created.
- **Materials only** — resources/labour are excluded from feasibility.
- Multi-item mode passes `items` as **URL-encoded JSON** in the query string (`[{"fg_code","qty"}]`), not a POST body; shared RM/PM are summed across FGs (`used_in` shows which FGs draw on each).
- Negative available/max reflects SAP oversell in the chosen warehouse — widen "Stock from" or use the transferable hint.

## Related
- [[stock-available]], [[daily-production]], [[non-moving-stock]], [[warehouses]], [[OIH]]
