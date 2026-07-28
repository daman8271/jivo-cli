---
title: Hidden Customer Sales
route: /realise/hidden-sales/
type: page
endpoints: [hidden-sales]
tags: [jivo, control-panel, sales, hidden-sales]
---
# Hidden Customer Sales

## Purpose
Surfaces sales invoices that were **flagged hidden in SAP** (`U_ARNO = 'H'`) and therefore **excluded from the dashboard's headline "Done"** figure. Lets ops/finance see how much real sales value is being held out of the counted numbers, and drill it by customer, item, cost centre, date or status. Oil company only.

## What it shows
- **KPI cards** — Hidden Value (₹), Premium value, Commodity value, Hidden Litres, Invoices (count), Customers (count with hidden sales).
- **Toolbar** — From/To dates (default current month → today); **Last (months)** shortcut (overrides From/To, fetches last N months for month-wise drill); Fetch; Type (Premium/Commodity); State; Main Group; Search (customer/item/cost center/doc); **Metric** multi-select (Value ₹ / Litres / Quantity / Realise ₹/L, stacked in each cell); multi-level **Drill By**; Export Excel.
- **Month-wise pivot** — collapsible tree, one column per month in the window plus Grand Total and Avg (per-month average); default drill = Customer › Item.

## Data sources
- [[hidden-sales]] — single POST returning the flat list of hidden invoice lines for the range; all KPIs, month bucketing, filtering and drill are client-side.
- Excel download posts to the shared `export-xlsx/` endpoint (file/WRITE — not probed).

## Key fields & columns
- **Hidden Value** → Σ line `value` (taxable ₹) of hidden invoices.
- **Litres** → `litres` (qty × pack size); **Quantity** → `qty` (boxes/pieces).
- **Realise ₹/L** → `value / litres` (see [[REALISE]]).
- **Cost Center** → SAP `OcrCode` (variety, e.g. CANOLA).
- **Status** → Open / Closed invoice.
- **Prem/Comm** → `u_type` Premium vs Commodity.
- Drill dimensions: Customer, Item Name, State, [[Main Group]], Prem/Comm, Cost Center, Date, Status.

## Notes / gotchas
- **"Hidden sales"** in this ERP = invoices where the SAP user-field `U_ARNO` is set to `'H'`. They are genuine billed sales but are deliberately **kept out of the Realise dashboard's "Done"** total — this page is the audit view of exactly what's excluded and how much.
- **Last (months)** overrides the From/To pickers when set (end = today, start = 1st of the N-1 months-ago month) — useful with the Date drill for a month-wise view.
- Oil only — there is no Beverages toggle here.
- Access gated by the `hidden_sales_viewer` group / `can_hidden_sales` permission.

## Related
[[compare-sales]], [[sales-cn]], [[REALISE]], [[Main Group]]
