---
title: Sales Document Flow
route: /realise/sales-flow/
type: page
endpoints: [sales-flow, sales-flow-open-items, export-xlsx]
tags: [jivo, control-panel, sales, flow-dispatch]
---
# Sales Document Flow

## Purpose
Traces each day's sales **end-to-end through the SAP Business One document chain** so a JIVO ops user can see, per customer, exactly how an order became an invoice. For every party it lays out the linked chain **Sales Quotation → Sales Order → Invoice** together with the invoiced volume, and flags which documents are still **open** (pending delivery/invoicing) and **who created each document** — the automated **[[oms]]** software (B1i) or a named SAP user who keyed it by hand. Default view is *yesterday*. This is the operational companion to [[dispatch-details]] (which picks up after the invoice, at the lorry).

## What it shows
- **KPI cards** (computed client-side from the returned rows): **Invoices** (distinct invoice numbers), **Total Litres/Boxes** (invoiced volume, abbreviated e.g. "1.20 L"), **Parties** (distinct `card_code` billed), **Quotations** (distinct linked quotation numbers).
- **Filter bar:**
  - **Company** segmented toggle — **Oil** vs **Beverages** (drives the `company` field; each has its own SAP company DB). Switching refetches. Oil is measured in **Litres**, Beverages in **Boxes** — see [[segments-oils-beverages]].
  - **From / To** date inputs + a **Yesterday** reset button (defaults both to yesterday).
  - **Fetch** button (re-hits the API).
  - **Documents** segmented toggle — **Both** vs **Open Doc**. This is a *pure client-side view filter* (no refetch): "Open Doc" keeps only rows whose Sales Order is still open (`order_open`). Rows raised directly with no order drop out.
  - **Search** box — free text over party / doc numbers / source (matches "OMS" or the SAP username).
  - **Export Excel** — posts the current filtered rows to [[export-xlsx]] (WRITE/file endpoint — builds an `.xlsx`; not probed).
- **Main table** — one row per document chain, columns: Date, Party Name, Sales Quotation No., Sales Order No., Invoice No., **LTR/Boxes**. Sortable headers; sticky **TOTAL** footer row summing volume. Default sort is by `invoice_no`.
- **Per-document chips:** a green **Open** / grey **Closed** status chip, plus a **source tag** — indigo **OMS** pill (created by the OMS/B1i software) or a grey pill showing the **SAP username** who keyed it.
- **Open-items drill modal:** an **open** quotation/order number is clickable (dotted underline). Clicking it opens a popup listing that document's still-open line items (item code, name, **Open Pcs**, **Open Qty**) with a total, fetched from [[sales-flow-open-items]].

## Data sources
- [[sales-flow]] — `POST /realise/api/sales-flow/`: the day's document chains (rows array) + `measure` (Litres/Boxes). Primary feed.
- [[sales-flow-open-items]] — `POST /realise/api/sales-flow/open-items/`: line-level open quantities for one open quotation/order (drill modal).
- [[export-xlsx]] — `POST /realise/api/export-xlsx/`: server-side Excel builder for the current view (file download; WRITE-side, not probed).

## Key fields & columns
- **Party Name / `card_code`** → customer master name and SAP business-partner code (e.g. `CUSTA000606`). See [[customer-master]].
- **Sales Quotation No.** (`quotation_no`) → SAP OQUT document number; blank if the order was raised without a quotation.
- **Sales Order No.** (`order_no`) → SAP ORDR document number; blank if the invoice was raised directly. Relates to [[order-in-hand]] (OIH) — open orders are unfulfilled demand.
- **Invoice No.** (`invoice_no`) → SAP OINV A/R invoice number; the billed document that realises revenue (see [[sales-dashboard]]).
- **LTR / Boxes** (`qty`) → invoiced volume in the company's unit (`measure`): Litres for Oil, Boxes for Beverages.
- **Open vs Closed** (`quotation_open` / `order_open` / `invoice_open`) → whether that document still has unprocessed (open) lines in SAP. Blank quotation/order = document was skipped (raised directly).
- **Source** (`*_src`) → `{oms:bool, label, user}`. `oms:true` = created by the **[[oms]]** software (B1i integration); otherwise `label`/`user` is the SAP user who keyed it (e.g. MANSI, SUMIT).

## Notes / gotchas
- "Open Doc" filter and search/sort are **client-side only** — all rows for the date range come down in one fetch; only Company and date changes refetch.
- Blank Quotation and/or Order columns are **expected**, not missing data: it means that step of the chain was skipped (direct order / direct invoice).
- The header REALISE ticker (₹/L) at top is global chrome, not specific to this page — see [[sales-dashboard]].
- Volume unit flips with the Company toggle; KPI label and column header re-render from the API's `measure`.
- Access gated by the `sales_flow_viewer` group / `can_sales_flow` permission.

## Related
[[dispatch-details]], [[sales-flow]], [[sales-flow-open-items]], [[export-xlsx]], [[order-in-hand]], [[sales-dashboard]], [[oms]], [[customer-master]], [[segments-oils-beverages]]
