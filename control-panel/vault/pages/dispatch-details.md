---
title: Dispatch Details
route: /realise/dispatch-details/
type: page
endpoints: [dispatch-details, export-xlsx]
tags: [jivo, control-panel, sales, flow-dispatch, logistics]
---
# Dispatch Details

## Purpose
The **logistics tail** of the sales document flow: for every A/R invoice in a date range it shows **how the goods physically left the warehouse** — dispatch date, the transporter's **bilty** (lorry receipt / consignment note), vehicle number and driver's mobile. A JIVO ops user uses this to confirm what has actually been dispatched vs merely invoiced, to chase pending dispatches, and to look up truck/driver contact for a given invoice. It picks up exactly where [[sales-flow]] ends (at the invoice).

## What it shows
- **KPI cards** (computed client-side from the rows): **Invoices** (A/R invoices in range), **Dispatched** (invoices that have a bilty number), **Customers** (distinct `code`), **Transporters** (distinct transporter names).
- **Filter bar:**
  - **From / To** date inputs — default range is **current month-to-date**, auto-fetched on load.
  - **Fetch** button.
  - **Search** box — free text over customer / invoice no / bilty / vehicle / transporter / driver mobile.
  - **Export Excel** — posts the current (filtered + sorted) view to [[export-xlsx]] (file download; WRITE-side, not probed).
  - Live **count** of invoices in the current view.
- **Main table** — one row per invoice, columns: Inv Date, Customer (+ code chip), Inv No., Dispatch Date, Bilty Date, Bilty No., Transporter, Vehicle No., Driver Mobile No. Sortable headers (default newest invoice date first). Dates are re-formatted to `DD-MM-YYYY` for display. Empty logistics fields render as a dash "—" (invoice raised but not yet dispatched).

## Data sources
- [[dispatch-details]] — `POST /realise/api/dispatch-details/`: one row per A/R invoice in the range with its dispatch/bilty/vehicle/driver metadata. Sole feed.
- [[export-xlsx]] — `POST /realise/api/export-xlsx/`: server-side Excel builder for the current view (file download; WRITE-side, not probed).

## Key fields & columns
- **Inv Date** (`inv_date`) → SAP A/R invoice (OINV) posting date.
- **Customer / code** (`name` / `code`) → business-partner name + SAP card code (e.g. `CUSTA001073`). See [[customer-master]].
- **Inv No.** (`inv_no`) → SAP invoice document number (ties this row back to the Invoice column in [[sales-flow]]).
- **Dispatch Date** (`dispatch`) → date goods physically dispatched; blank if not yet dispatched.
- **Bilty Date / Bilty No.** (`biltydate` / `bilty`) → date and number of the **bilty** (transporter's Goods/Lorry Receipt — the consignment note). Presence of a bilty is the app's definition of "Dispatched".
- **Transporter** (`transporter`) → freight carrier name (e.g. "Mahaveer Transport").
- **Vehicle No.** (`vehicle`) → truck registration (e.g. `HR67C1036`).
- **Driver Mobile No.** (`mobile`) → driver contact number.

## Notes / gotchas
- Search, sort and KPI recomputation are **client-side** over one fetched result set; only date-range + Fetch hits the server.
- Many rows have empty dispatch/bilty/vehicle fields — that's an **invoiced-but-not-yet-dispatched** invoice, not missing data; the "Dispatched" KPI counts only those with a bilty.
- Unlike [[sales-flow]] there is **no Company (Oil/Beverages) toggle** — this endpoint takes only a date range.
- Access gated by the `dispatch_details_viewer` group / `can_dispatch_details` permission.

## Related
[[sales-flow]], [[dispatch-details]], [[export-xlsx]], [[customer-master]], [[sales-dashboard]]
