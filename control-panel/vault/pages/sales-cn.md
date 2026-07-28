---
title: Sales vs Credit Notes
route: /realise/sales-cn/
type: page
endpoints: [sales-cn]
tags: [jivo, control-panel, sales, credit-notes]
---
# Sales vs Credit Notes

## Purpose
Lets a JIVO ops/finance user see **gross sales netted against credit notes** for a company (Oil or Beverages) over any date range, and drill the gap by group, state, person, product, item or customer. It answers: how much of our billed sales is being clawed back by returns and claims, and where? Net Sales = Total Sales − Total CN.

## What it shows
- **Company toggle** — Oil / Beverages (Oil measures in Litres, Beverages in Boxes).
- **KPI cards** — Total Sales (gross OINV invoices), Total CN (Goods + Services), Net Sales.
- **Toolbar** — From/To date pickers (default = 1st of current month → today); Fetch; Measure toggle (Revenue ₹ / Litres|Boxes); Type filter (Premium / Commodity — oil only); free-text Search (customer / item / person); multi-level **Drill By** picker; Export Excel.
- **Pivot table** — collapsible tree with columns: Total Sales, Total CN, CN for Goods, Claim for Services, Net Sales; grand-total row pinned at the bottom.

## Data sources
- [[sales-cn]] — the single POST that returns the flat sales-vs-CN row list for the chosen company & range; all pivoting, KPIs and filtering happen client-side.
- Excel download posts the rendered pivot to the shared `export-xlsx/` endpoint (file/WRITE — not probed).

## Key fields & columns
- **Total Sales** → gross billed sales (SAP OINV invoices), `sales_rev` (or `sales_qty` in qty mode).
- **Total CN** → all credit notes = CN for Goods + Claim for Services (revenue mode); in qty mode only Goods count (services have no quantity).
- **CN for Goods** → `cng_rev`/`cng_qty` — credit notes for **physical product returns**.
- **Claim for Services** → `cns_rev` — credit notes for **services**: discounts, FOC (free-of-charge), samples, scheme claims. No quantity.
- **Net Sales** → `Total Sales − Total CN`.
- **Contact Person** → not the raw invoice UDF; the page maps `main_group`+`state` to the assigned **territory owner** (same TERRITORY map as [[compare-sales]]), e.g. `GT|DELHI → SUNNY JI`, `E-COMMERCE → PRABHU SIR`.
- Dimensions: [[Main Group]] (GT/MT/ROI/ECOM/…), State, Contact Person, Product, Item Name, Customer.

## Notes / gotchas
- **"Sales vs CN"** = gross sales vs credit notes. Two kinds of CN: **CN for Goods** (returns of product) and **Claim for Services** (money-only adjustments — discounts/FOC/samples). Netting both off gross gives the real realised sales.
- Beverages has no Premium/Commodity split (`has_type:false` hides the Type filter) and measures in **Boxes**, not Litres.
- Litres/Boxes mode blanks the "Claim for Services" column because service claims carry no quantity.
- Access gated by the `sales_cn_viewer` group / `can_sales_cn` permission.

## Related
[[compare-sales]], [[hidden-sales]], [[credit-note]], [[Main Group]], [[REALISE]]
