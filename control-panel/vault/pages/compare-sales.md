---
title: Compare Sales
route: /realise/compare-sales/
type: page
endpoints: [compare-docs]
tags: [jivo, control-panel, sales, analytics]
---
# Compare Sales

## Purpose
A **month-over-month sales pivot** for oil. A JIVO sales user picks a look-back window (last N months) and a drill dimension, then compares **Litres, Realise (₹/L), or both** across months — spotting growth/decline by group, state, territory owner, product, item or customer. Every value cell is clickable to see the underlying invoices.

## What it shows
- **Toolbar** — Last (months) input (default 6) with "Incl. current month" toggle; Fetch; Type (All/Premium/Commodity); Customer & Item search boxes; Main Group multi-select; Pack Size multi-select; **Compare** mode (Litres / Realise / Both); multi-level **Drill By**; Top-N items (when Item is the first drill); Export Excel.
- **Pivot table** — collapsible drill tree; one column per month in the window + Grand Total + Avg Sales; TOTAL row pinned on top. Cells show the compare measure(s).
- **Multi-item Calculate** — tick items to compare their Litres/Revenue/Realise side by side.
- **Invoice drill modal** — click any month cell to open the invoices behind it (doc no, date, party, box qty, rate/bottle, taxable value, litres, realise ₹/L), each expandable to item lines.

## Data sources
- `/realise/api/sales-data/` — the main pivot data (start_date/end_date; owned by another slice, not documented here).
- [[compare-docs]] — invoice-level **drill-down** for a clicked month × dimension cell (returns documents + item lines).
- Excel download posts the rendered pivot to the shared `export-xlsx/` endpoint (file/WRITE — not probed).

## Key fields & columns
- **Litres** → sales quantity in litres per month bucket.
- **Realise (₹/L)** → revenue ÷ litres — the blended realisation rate; see [[REALISE]].
- **Grand Total** → sum across the window; **Avg Sales** → Grand Total ÷ number of months.
- **Contact Person** → mapped **territory owner** (group+state → owner via the TERRITORY map, e.g. `GT|PUNJAB → RAMINDER JI`, `ECOM → PRABHU SIR`), not the raw invoice sales-person.
- Drill dimensions: [[Main Group]], State, Contact Person, Product, Item Name, Customer.
- Drill-modal item fields: Box Qty, Rate/Bottle, Taxable Value, Litres, Realise ₹/L.

## Notes / gotchas
- The grid and the drill use **two different endpoints** — `sales-data/` builds the pivot, [[compare-docs]] fetches the invoices behind one cell (scoped to that single month + the active drill filters).
- "Incl. current month" unticked → window ends at the previous complete month.
- Top-N items only applies when Item is the first drill dimension.
- Access gated by the `compare_sales_viewer` group / `can_compare_sales` permission.

## Related
[[sales-cn]], [[hidden-sales]], [[compare-docs]], [[REALISE]], [[Main Group]]
