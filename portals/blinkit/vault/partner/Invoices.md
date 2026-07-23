---
title: Invoices
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Invoices

The **Invoices** section (route `/app/invoice-summary`, sidebar label "Invoices") is JIVO's
**primary-lane** view of what Blinkit actually received against its POs: goods-receipt notes
(GRNs) and vendor invoices. Where [[PO-Summary]] is "what Blinkit ordered", Invoices is "what
was booked/received and what discrepancies were found". The page carries a data-availability
note that **GRN data exists from April 2023** onward. In the SPA route map, `/invoice-summary`
is bucketed under `category:"payments"` with `ticketFilter:"PAYMENT"` — i.e. Blinkit groups
invoices with the money/settlement side of the relationship (feeds [[Payments]]). Each invoice
row drills into a per-invoice detail page at `/app/invoice-details/:vendorInvoiceId/:orderNumber`,
and every invoice is also reachable from its parent PO via the PO detail page's **Invoices** tab
(`PO_INVOICES_TAB_CLICKED`). Bulk export of the whole invoice/GRN table is done through the same
async report queue as Sales/SOH — the queued job type is **"Invoices Excel"**, delivered as
`bulk_invoice_csv-<id>.csv`.

## Subpages & tabs

- **Invoice summary table** — the landing grid of invoices/GRNs (`INVOICE_SUMMARY_VIEWED`,
  `INVOICES_VIEWED`).
- **Invoice detail drawer** — opens on a row (`INVOICE_SUMMARY_DRAWER_VISIBLE`) with three
  line-item tabs:
  - **All items** (`INVOICE_SUMMARY_DRAWER_ALL_ITEMS_VISIBLE`) — everything on the invoice.
  - **GRN items** (`INVOICE_SUMMARY_DRAWER_GRN_ITEMS_VISIBLE`) — what was actually received.
  - **Discrepancy items** (`INVOICE_SUMMARY_DRAWER_DISCREPANCY_ITEMS_VISIBLE`) — ordered-vs-received
    mismatches (short/excess/rejected).
- **Invoice detail page** — full route `/app/invoice-details/:vendorInvoiceId/:orderNumber`
  (per-invoice, keyed to its PO/order).
- **PO → Invoices tab** — the same invoices surfaced from within a PO's detail view
  (`PO_INVOICES_TAB_CLICKED`), linking [[PO-Summary]] ↔ Invoices.
- **"Download Bulk Invoice Data" modal** — a green top-right action ("Download Bulk Invoice data
  CSV") with three source tabs (from live GUI capture, Flow 30):
  - **Invoices** (the used tab) · **PRN** · **DN** — PRN (Purchase Return Note) and DN
    (Delivery/Debit Note) are sibling document types, candidate future sub-flows.

## Filters & columns (what the table shows)

**Filters** (from the analytics enum — three filter surfaces exist: `INVOICE_FILTERS_APPLIED`,
`INVOICE_TABLE_FILTERS_APPLIED`, `INVOICE_AGGREGATED_FILTERS_APPLIED`). The bulk-export modal
exposes the key one, a **Date Type** radio:
- **Grn Date** (default used) · **Due Date** · **Payment Date**
- plus a **date range** picker (DD-MM-YYYY in the UI; house convention = 1st-of-month → T-1).

**Columns / fields.** Human-readable column labels are not present in this captured bundle (the
invoice module's column defs and label strings live in a lazily-loaded chunk), so the exact grid
headers are *to confirm via live capture*. From the live bulk-invoice CSV (Flow 30) the exported
row carries at least:
- `PO_NUMBER`, `GRN_DATE`, `FORMAT` (= `BLINKIT`), plus item/qty/value fields (full schema TBC).

Detail-drawer line items are split into All / GRN / Discrepancy views (see tabs above), implying
per-SKU fields like ordered qty, GRN'd qty, and a discrepancy delta.

**Per-invoice document downloads** (detail drawer buttons, from the enum):
- **GRN file** (`INVOICE_GRN_FILE_REQUESTED`) · **DN / delivery note** (`INVOICE_DN_FILE_REQUESTED`)
  · **Scanned invoice** (`INVOICE_SCANNED_INVOICE_FILE_REQUESTED`) · **ZIP of documents**
  (`INVOICE_ZIP_DOWNLOAD_REQUESTED`) · **Bulk table export** (`INVOICE_BULK_DATA_REQUESTED`).
- Icon set confirms document actions: `download-invoice`, `download-receipt`.

## API endpoints

Exact invoice REST paths are **not literal strings** in the captured SPA bundle (paths are built
from minified fragments), so only the shared report-queue chain below is *proven* (from live curl
captures + `blinkit-cli`). Invoice-specific data/document endpoints are marked to-confirm rather
than invented. All auth = header tokens (`x-api-key` + `token`/`access_token`, `x-entity-id:1117`,
`x-entity-type:manufacturer`, base `https://www.partnersbiz.com`), same as every other section.

| METHOD | path | purpose | read/write |
|---|---|---|---|
| POST | `/v1/report-requests/` (body `{}`) | List the async report queue; the invoice bulk job appears as `type:"Invoices Excel"`. Poll here for state=`success`. | **READ** (proven — list only, despite POST verb) |
| GET | `/v1/report-requests/download//{id}/` | Mint a fresh ~15-min presigned S3 URL for a completed "Invoices Excel" report. (literal double-slash is how the app builds it) | **READ** (proven) |
| GET | `<presigned S3 url>` | Download `bulk_invoice_csv-<id>.csv` — no auth (presigned). | **READ** (proven) |
| GET | invoice-summary list / detail feed — `endpoint: to confirm via live network capture` | Fetch the invoice-summary table rows + the detail-drawer line items (All / GRN / Discrepancy). Pure read. | **READ** (path unconfirmed) |
| GET | per-invoice document links (GRN / DN / scanned invoice / ZIP) — `endpoint: to confirm via live network capture` | Retrieve stored invoice documents. Pure read. | **READ** (path unconfirmed) |

**Out of scope (writes / state-changing) — do NOT call from a read-only CLI:**
- `POST /v1/reports/<invoice-bulk>-excel/` — *generate* a fresh bulk-invoice/GRN export.
  Parallels the proven `POST /v1/reports/sales-details-excel/` and `.../soh-details-excel/`
  pattern and produces the `type:"Invoices Excel"` queue row, but the **exact invoice path is
  unconfirmed** (`endpoint: to confirm via live network capture`). It is a POST that **enqueues a
  job and also fires a "registered email" delivery**, i.e. it mutates server state — treat as
  OUT-OF-SCOPE. A strict read-only CLI must only *consume* already-generated Invoices Excel rows,
  never trigger new ones.
- Any invoice create/edit/delete or PO-scheduling invoice mutations (`PO_SCHEDULING_ADD_INVOICE`,
  `PO_SCHEDULING_EDIT_INVOICE_DETAILS`, `PO_SCHEDULING_DELETE_INVOICE_CLICKED`,
  `PO_SCHEDULING_INVOICE_OR_SERIALIZED_DATA_UPLOADED`) — these are vendor-side write actions on the
  scheduling/ASN flow, **OUT-OF-SCOPE**.

## Real data seen (evidence)

- **Live report queue** (2026-07-24 known-state): 20 reports, distinct types include **"Invoices
  Excel"** alongside Bulk PO Excel, SOH Details Excel, Sales Details Excel — all state `success`.
  Confirms the bulk-invoice export lands in the same `/v1/report-requests/` queue this CLI already
  reads.
- **Flow 30 manual GUI run (2026-07-11, ecomcliauto/blinkit/FLOWS.md):** `/app/invoice-summary` →
  "Download Bulk Invoice Data" → Date Type `Grn Date`, range `01-07-2026 → 11-07-2026` → queue row
  `Date Type: grn_date, Start 01-07-2026, End 11-07-2026`, success in ~5s → downloaded
  `bulk_invoice_csv-<id>.csv` (~16 KB) → parsed **69 rows** (columns incl. `PO_NUMBER, GRN_DATE,
  FORMAT=BLINKIT`) → uploaded to `ecom.jivo.in/uploaders?dataset=primary&platform=blinkit` with
  Primary type = **GRN** → Insert 69/0/0.
- **No dedicated invoice/GRN capture file exists yet** in `ecomcliauto/captures/blinkit/` (only
  sales/soh/report-requests/download/brandcentral captures) — the invoice request payload is
  *uncaptured*, which is why the generate path stays "to confirm".
- **`blinkit-cli` does not yet implement invoices** — its commands are `doctor`, `reports`,
  `sales pull`, `soh pull`, `brandfund pull`, `ads pull`. Invoice/GRN is a documented-but-unbuilt
  flow (Flow 30). The auth + `report-requests` poll + `download//{id}/` chain is fully reusable.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming already-generated data (no POST-generate, no document mutation):
- `blinkit invoices reports` — list `/v1/report-requests/` filtered to `type == "Invoices Excel"`
  (id, state, grn/due/payment date-type, date window, filename). Pure READ.
- `blinkit invoices download <report_id> [--out FILE]` — mint the presigned URL via
  `GET /v1/report-requests/download//<id>/` and fetch `bulk_invoice_csv-<id>.csv`. Pure READ.
- `blinkit invoices summary [--from --to]` — fetch the invoice-summary table rows once the
  list/detail GET endpoint is confirmed via live capture. Pure READ (path TBC).
- `blinkit invoices detail <vendorInvoiceId> <orderNumber>` — the per-invoice drawer data with
  All / GRN / Discrepancy line items (path TBC). Pure READ.
- `blinkit invoices docs <vendorInvoiceId>` — list/fetch stored GRN / DN / scanned-invoice / ZIP
  document links (paths TBC). Pure READ.

Explicitly **excluded** from the read-only surface: triggering a fresh bulk-invoice export
(`POST /v1/reports/<invoice-bulk>-excel/`) and any PO-scheduling invoice add/edit/delete — those
are writes.

## Connections

- Portal hub: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Primary-lane sibling / parent orders: [[PO-Summary]] (PO detail page has an Invoices tab; GRNs
  are booked against POs)
- Bulk export goes through the shared queue: [[Report-Requests]] (type "Invoices Excel")
- Grouped with settlement in the route map (`category:"payments"`): [[Payments]]
- Contrasts with the secondary/sell-out lane: [[Sales]] · [[Stock-on-Hand]]
- Future sibling document types surfaced in the bulk modal (PRN / DN tabs): candidates for
  [[EDI-Integration]] / new notes
