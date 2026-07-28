---
title: Realise Calculator
route: /realise/realise-calculator/
type: page
endpoints: [realise-calculator-items, rate-list, rate-list-save, realise-calculator-upload, realise-calculator-order-upload, realise-calculator-export]
tags: [jivo, control-panel, calculator-ratelist]
---

# Realise Calculator

## Purpose
A what-if pricing workbench for JIVO sales/pricing ops. You build a list of SKUs with their retailer price and trade terms (super-stockist %, distributor %, GST %, pcs/box, flat discount, scheme litres) and the calculator back-solves the **net ex-factory realisation in ₹ per litre** ([[REALISE]]) for each line, plus a blended realisation and total revenue for the plan. It answers: *"if we set this retailer price and give these margins + this scheme, what ₹/L do we actually realise, and how does plan A compare to plan B / old order vs new order?"* Finished plans can be **saved** to the [[rate-list]] (tagged by state) or **exported to Excel**.

## What it shows
Top ticker shows the current live blended [[REALISE]] (e.g. ₹171.07/L). The calculator card has three tabs:

- **Planning Grid** — one editable table. Each row = one SKU. Columns: Item (SAP picker), Retailer ₹/piece, SS %, Dist %, GST %, Pcs/Box, Flat Disc ₹/box, Box Ltrs, Scheme L, To-be-sale (L). Under each row a results strip shows the margin-waterfall steps (SS Rate, Dist Rate, Ex-GST, Box Value, Net Box, Total Ltr) and the computed **RELISE ₹/L** and **Revenue ₹**. A footer blends the whole grid; summary chips show Total To-be-sale, Blended Realise, Total Revenue.
- **Compare** — two independent grids side by side: **Existing Plan (A)** vs **New Plan (B)**. Bottom KPIs: Plan A Realise, Plan B Realise, A−B Realise, A−B Revenue, (A−B) × Plan B volume.
- **New vs Old Order** — same engine, **Old Order** vs **New Order** grids (Old is typically Excel-uploaded, New is edited); KPIs for New − Old realise & revenue.

Actions: **+ Add row**, **Clear all**, **Save Result** (→ Rate List, choose state + scope), **Export Excel**, **Upload Excel** (fill rows from an `.xlsx` with an *Item Code* column).

**SAP item picker** (modal): cascades **SKU / Size → Variety → Item**, or free-text search. Picking an item auto-fills the item name/code, Pcs/Box and Box Litres from the SAP master ([[realise-calculator-items]]) and defaults GST to 5%.

## Data sources
- [[realise-calculator-items]] — GET; the SAP finished-goods master (374 items) that powers the item picker and auto-fills pcs/box & box litres.
- [[rate-list]] — GET `?id=<n>`; loads a previously saved result back into the grids when the page is opened as `?load=<id>`.
- [[rate-list-save]] — POST (**WRITE**); "Save Result" persists the current plan(s) to the Rate List.
- [[realise-calculator-upload]] — POST (**WRITE/upload**); fills the Planning Grid / a Compare grid from an uploaded `.xlsx`.
- [[realise-calculator-order-upload]] — POST (**WRITE/upload**); fills both Old + New Order grids from an order `.xlsx`.
- [[realise-calculator-export]] — POST (**EXPORT**); returns the plan(s) as a formatted `.xlsx` download.

## Key fields & columns
The full margin waterfall is computed client-side per row (`rowCalc`), inputs → derived:

| Field | Meaning |
|---|---|
| Retailer ₹ | Retailer price **per piece** (the top of the chain) |
| SS % | Super-stockist margin backed out: `SS Rate = Retailer ÷ (1 + SS%)` |
| Dist % | Distributor margin backed out: `Dist Rate = SS Rate ÷ (1 + Dist%)` |
| GST % | Tax removed: `Ex-GST = Dist Rate ÷ (1 + GST%)` (defaults to 5) |
| Pcs/Box | Pieces per box (SAP `SalFactor2`); `Box Value = Ex-GST × Pcs/Box` |
| Flat Disc ₹ | Flat discount **per box**: `Net Box = Box Value − Flat Disc` |
| Box Ltrs | Saleable litres in the box (SAP `box_litres`) |
| Scheme L | Free scheme litres given away with the box |
| **Total Ltr** | `Box Ltrs + Scheme L` — the litres the net value is spread over |
| **RELISE ₹/L** | `Net Box ÷ Total Ltr` — the [[REALISE]] this row yields |
| To-be-sale (L) | Planned volume in litres for this SKU |
| **Revenue ₹** | `Realise × To-be-sale` |

**Blended Realise** = Σ Revenue ÷ Σ To-be-sale across all rows. Scheme litres dilute realisation; margins and GST are stripped out because JIVO realises the ex-factory net, not the retailer shelf price.

## Notes / gotchas
- Label in the UI is spelled **"RELISE"** (typo carried through the code) but means [[REALISE]].
- Item `type` on picker chips: **P** vs **C** (SAP item classification) — cosmetic only, does not change the maths.
- All maths is client-side JS; the server endpoints only serve the item master, persist/reload saved results, parse Excel uploads, and render the Excel export.
- Saving requires a **scope** (`GRID`, `ORDER`, `A`, `B`, `BOTH`) so the result reloads into the correct tab/grid later.
- Read-only recon: `save/`, `upload/`, `order-upload/`, `export/` are all mutating/file endpoints — documented from page JS, never executed.

## Related
[[rate-list]] · [[realise-calculator-items]] · [[rate-list-save]] · [[realise-calculator-export]] · [[REALISE]] · [[sales-dashboard]] (Sales dashboard)
