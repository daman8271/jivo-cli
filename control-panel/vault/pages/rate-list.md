---
title: Rate List
route: /realise/rate-list/
type: page
endpoints: [rate-list, rate-list-save, rate-list-delete]
tags: [jivo, control-panel, calculator-ratelist]
---

# Rate List

## Purpose
A saved library of [[realise-calculator]] results. Whenever a pricing scenario is worked out in the Realise Calculator it can be saved here, **tagged by state**, so JIVO ops can keep and revisit approved rate/scheme plans per market. Each saved entry can be re-opened ("Load & Edit") back into the calculator, or deleted. This page is **read/browse only** for the plans — new entries are created from the calculator's Save button, not here.

## What it shows
- A filter bar: **State** dropdown (populated from the states present in saved results) + a **Search** box (matches result name) + a live count of saved results.
- A list of collapsible **result cards**. Each card header shows the result **name**, a **state** chip, a **scope** chip (Planning Grid / Old + New Order / Existing + New / Existing Plan / New Plan), the created-at timestamp + creator, a **Load & Edit** button and a **Delete** (✕) button.
- Expanding a card renders each saved **plan** as a table (Item, Retailer ₹, GST %, Pcs/Box, Box Ltrs, Scheme, To-be-sale, **RELISE ₹/L**, Revenue ₹) with a blended footer, plus **compare KPIs** when the result stored a comparison (Plan A/B realise, A−B realise, A−B revenue, (A−B) × B volume).
- Currently the store is **empty** (`rows: [], states: []`) — the empty state reads *"No saved results. Save one from the Realise Calculator → Compare tab."*

## Data sources
- [[rate-list]] — GET; loads every saved result (`rows[]`) plus the distinct `states[]` for the filter.
- [[rate-list-save]] — POST (**WRITE**); the actual create — invoked from the [[realise-calculator]] Save dialog, not this page.
- [[rate-list-delete]] — POST (**WRITE**); the ✕ button deletes a saved result by `id` (with a confirm prompt).

"Load & Edit" navigates to `/realise/realise-calculator/?load=<id>`, which re-fetches that single row via [[rate-list]] `?id=<id>` and hydrates the grids.

## Key fields & columns
Each saved-result row:

| Field | Meaning |
|---|---|
| `id` | Saved-result primary key |
| `name` | User-given result name |
| `state` | Indian state tag (from a fixed 24-state list) |
| `scope` | Which calculator tab it came from → `GRID`, `ORDER`, `A`, `B`, `BOTH` |
| `created_at` | Timestamp string |
| `created_by` | Username who saved it |
| `payload.plans[]` | One or two plans, each `{name, rows[], totals}` |
| `payload.plans[].rows[]` | Per-SKU line: item, code, retailer, ss, dm, gst, pcsbox, disc, boxltr, scheme, sell + derived realise/revenue |
| `payload.plans[].totals` | `{totSell, revSum, blend}` — plan blended [[REALISE]] |
| `payload.compare` | `{blendA, blendB, diffRealise, diffRevenue, aMinusBxBvol}` (only for BOTH/ORDER scopes) |

Scope chip labels: `GRID` → "Planning Grid", `ORDER` → "Old + New Order", `BOTH` → "Existing + New", `A` → "Existing Plan", anything else → "New Plan". See [[REALISE]] for the ₹/L metric.

## Notes / gotchas
- The page cannot create results — only the [[realise-calculator]] can. This page lists, filters, loads and deletes them.
- Same "RELISE" spelling as the calculator; it is [[REALISE]].
- Delete and Save are mutating; documented from page JS only (read-only recon).

## Related
[[realise-calculator]] · [[rate-list]] · [[rate-list-save]] · [[rate-list-delete]] · [[REALISE]]
