---
title: Payments
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Payments

The **Payments** section is Blinkit's **money / settlement view** of the JIVO ↔ Blinkit
relationship — what Blinkit owes and has paid against received goods, what it has **deducted**
(brand fund, price variance), and what it has **charged back** (fees, penalties, adjustments).
It is the payout counterpart to the primary lane: [[PO-Summary]] is "what Blinkit ordered",
[[Invoices]] is "what was received/booked", and Payments is "what actually gets paid, minus
deductions, minus charges". For JIVO this is Jivo Wellness Pvt. Ltd. (`x-entity-id=1117`, type
`manufacturer`).

**Two faces of the same section.** On **mobile** the app has a two-item bottom nav bar —
`[{key:"orders",label:"Orders",path:"/app/orders"}, {key:"payments",label:"Payments",path:"/app/payments"}]`
— so `/app/payments` is the mobile Payments landing (the invoice/payment list). On **desktop**
the sidebar splits the same money surface into first-class items whose Help/Support tickets are
all pre-filed under `category:"payments"`: **"Invoices"** (`/app/invoice-summary`, component
`InvoiceSummaryDashboard`) and **"Fees & Charges"** (`/app/fees-charges`, component
`FeesAndChargesEntryPoint`), plus the **Brand Fund** pages (`/app/brand-fund/*`). Confirmed by
the route map (`{path:"payments", element:<Payments/>}`), the nav config, and the help-category
map (`"/invoice-summary":{category:"payments",ticketFilter:"PAYMENT"}`).

**Honest scope note.** Unlike most sections, the Payments feature code **is** captured — it lives
in the code-split chunk `captures/partner/js/useFirebasePageTracking-CGSyAZ_Q.js` (≈5 MB), **not**
in `index.js` (which only holds the router/shell). That chunk contains the real endpoint
constants (built as `` `${hostUrl.VendorConsoleEndpoint}<path>` ``, where
`VendorConsoleEndpoint = window.VENDOR_CONSOLE_API_URL = https://www.partnersbiz.com/`), the
column defs, the filter tabs, and the payment-state enums — so the endpoints below are **read out
of the bundle, not invented**. Exact request/response bodies still want a live network capture to
lock down, and are flagged where so.

## Subpages & tabs

Payments is a hub over three pillars:

1. **Invoices / payment status** (`/app/payments` on mobile · `/app/invoice-summary` on desktop,
   title "Invoices"). The invoice list carries **payment-status filter tabs**:
   `[{label:"Last 1 Month",key:"last_1_month"}, {label:"All",key:"all"}, {label:"Paid",key:"paid"},
   {label:"Upcoming",key:"upcoming"}]`. A row opens the **invoice/payment detail page**
   (`/app/invoice-details/:vendorInvoiceId/:orderNumber`; mobile back → `/app/payments`, desktop
   back → `/app/invoice-summary`) with collapsible sections:
   - **Invoice Details** — Invoice Amount (`invoice_amount_before_tax`), GRN Amount
     (`total_grn_amount`), Discrepancy Amount (`total_dn_amount`, shown red), footer **Approved
     Amount** (`net_payable`).
   - **Deductions** — Brand Fund (`brand_fund`), Price Variance (`price_variance`), footer **Total
     Deductions** (`total_deductions`).
   - **Totals** — Total Approved Amount (`approved_amount`), footer **Net Payable**
     (`total_payout_amount`).
   - A **payment-state banner**: `payment_state === "PAID" ? "PAYMENT COMPLETED" : "PAYMENT PENDING"`,
     plus a **UTR number** field and a **View GRN Details** sheet.
2. **Fees & Charges** (`/app/fees-charges`, title "Fees & Charges"). Header sub-text:
   *"Review fees, penalties, waivers and dispute status."* A charges table with a
   **granularity** toggle (Monthly / Weekly / Daily → `GRAN_MAP={monthly:"month",weekly:"week",
   daily:"day"}`), a date-range picker, and status views incl. **Disputed / Waived / Pending**.
   Each row is an adjustment/chargeback with a **"Raise a Dispute"** action (a write —
   out of scope).
3. **Brand Fund** (`/app/brand-fund`, `/app/brand-fund/daily-summary`,
   `/app/brand-fund/sheet-history/:offerType`, and single/bundle detail routes
   `/app/brand-fund/sheet-history/{single|bundle}/details/:sheetId`). Shows the promotional
   co-funding JIVO commits per SKU × city that later shows up as an invoice **deduction**. Sheet
   history tables + a per-city drill-down modal.

## Filters & columns (what the table shows)

**Invoice / payment list** (desktop `InvoiceSummaryDashboard`, mobile Payments list). Confirmed
column defs from the chunk: **PO Number** (`order_number`), **Invoice Number** (`invoice_number`),
**Invoice Value** (`invoice_amount_after_tax`), **Facility** (`facility_name`), **GRN Amount**
(`total_amount`), **Status** (`state`). Additional payment fields present as labels: **Invoice
Date**, **Due Date**, **Payment Date**, **Net Payable**, **Payment Advice**. Filter tabs =
Last 1 Month / All / Paid / Upcoming (above).
Payment-lifecycle enums baked in:
- `InvoiceStates`: DRAFT, OPEN, VERIFIED, REJECTED(3), UPDATED(4), PAID(5), COMPLETED(6),
  CLOSED(7) → `InvoiceStatusStringValues` = Draft / Open / Verified / Rejected / Completed.
- `DueStates`: `DUE="Due"`, `NOTDUE="Not Yet Due"`, `OVERDUE="Overdue"`, `PAID="Paid"`
  (ids: NOTDUE=1, OVERDUE=2, PAID=3).

**Fees & Charges table.** Columns: **Adjustment Type** (`adjustment_type`), **Reference ID**
(`reference_id`), **Payment amount** (`payment_amount`, rupees), **Total Cost**
(`total_amount` / `total_dn_amount`), **Status** (`status`). The adjustment-type map is the
useful legend:
`{BDPO:"Brand Fund", INCENTIVE_ON_SALE:"Brand Fund", ADVANCE_ADJUSTMENT:"Advance Recovery",
PURCHASE_RETURN_NOTE:"Purchase Return", OTHER_ADJUSTMENT:"Other Adjustment"}`. Status/dispute
strings seen: "Under Dispute", "Raise a Dispute", "Approval Pending", plus summary tiles from
`charges-summary` / `charges-stats`.

**Brand Fund tables.** Sheet-row table (`SingleHistoryTable`): **Item Id** (`retail_item_id`),
**Product Name** (`product_name`), **Funding Type** (`funding_type`), **Start Date** (`start_ts`),
**End Date** (`end_ts`), **City Value**, **Brand Comments** (`comments.sheet_comments`). Bundle
variant (`BundleDetailHistoryTable`) adds **Config** and **Offer Type**. Per-city modal:
**city** (`city_name` / "Pan India"), **Brand Fund Value** (`brandfund_value`), **Status**
(`approval_status`), **Approval Comments** (`comments.approval_comments`).

## API endpoints

Base = `https://www.partnersbiz.com/` (`VendorConsoleEndpoint`). Auth = header tokens
(`x-api-key: fe25a1da-…` + `token`/`access_token` `v2::<uuid>`, `x-entity-id:1117`,
`x-entity-type:manufacturer`, `service:partnersbiz`, `app_client:partnerbiz-web`), same as every
other section. Methods below are as wired in the chunk (`doHttpGet`/`doHttpPost`); several list
endpoints are POST-with-`{filters}` bodies but are **pure reads** (no state change), same idiom as
the proven `report-requests` list.

| METHOD | path | purpose | read?/write? |
|---|---|---|---|
| POST | `/v2/invoice/` (`INVOICE_LISTS`, body `{filters:{…}}`) | Invoice/payment list for the Paid/Upcoming/All/Last-1-Month tabs (`fetchInvoiceList`) | **READ** |
| POST | `/v1/invoices/` (`INVOICE_DATA`) | Full invoice/payment data feed | **READ** |
| POST | `/v1/invoices-lite/` (`INVOICE_DATA_LITE`) | Lightweight invoice list | **READ** |
| POST | `/v1/invoice/details/` (`INVOICE_DETAILS`) | Per-invoice payment breakdown (amounts, deductions, net payable, `payment_state`) | **READ** |
| POST | `/v1/aggregated-invoice-data/` (`AGGREGATED_INVOICE_DATA`) | Aggregated invoice/payment totals for the summary header | **READ** |
| POST | `/v1/invoice/grn-details/` (`INVOICE_ITEM_DETAILS`) | GRN line items behind an invoice (View GRN Details sheet) | **READ** |
| POST | `/v1/utr/invoices/` (`INVOICE_UTR`) | UTR (bank payment reference) per invoice — the actual settlement id | **READ** |
| POST | `/vendor_appointment/api/v1/invoice/fetch-invoice/` (`FETCH_INVOICES_FOR_POS`) | Fetch invoices tied to a set of POs | **READ** |
| POST | `/v1/invoice/download/` (`DOWNLOAD_INVOICE`) | Download a single invoice PDF (returns a file; no state change) | **READ** (POST verb, read effect) |
| GET | `/v1/vendor-reports/?start_date=&end_date=&download=zip` (`PAYMENT_ADVICE_DOWNLOAD`, blob) | **Payment Advice** — the remittance-advice ZIP for a date window | **READ** |
| GET | `/v1/client-po-details/{poId}/grn/pdf/` (`GRN_REPORT_PDF`) | GRN report PDF for a PO | **READ** |
| GET | `/v1/client-po-details/{poId}/fetch_discrepancy_note_pdf/` (`DISCREPANCY_NOTE_PDF`) | Discrepancy/debit-note PDF for a PO | **READ** |
| POST | `/v1/charges/` (`CHARGES_LIST_URL`, `fetchChargesList`) | Fees & Charges list (fees/penalties/adjustments) | **READ** |
| GET | `/v1/charges/{id}` (`CHARGES_DETAIL_URL`) | Single charge detail | **READ** |
| GET | `/v1/charges-summary/` (`CHARGES_SUMMARY_URL`) | Fees & Charges summary tiles | **READ** |
| GET | `/v1/charges-stats/` (`CHARGE_STATS_URL`) | Fees & Charges stat totals | **READ** |
| GET | `/v1/charges/filters/` (`CHARGES_FILTERS_URL`) | Filter values (facility, type, status) for the charges table | **READ** |
| GET | `/api/attributes/v1/brands-fund-summary/view/` (`dailySummaryCountUrl`) | Brand Fund daily summary view | **READ** |
| GET | `/api/attributes/v1/brands-fund-summary-count/view/` (`downloadDailySummaryUrl`) | Brand Fund summary count | **READ** (method to confirm) |
| GET | `/api/attributes/v1/brands-fund/get/` (`singleSheetDataRowWiseurl`) | Single brand-fund sheet, city-wise rows | **READ** (method to confirm) |
| GET | `/api/attributes/v1/brands-fund/get-sheet-rows/` (`singleSheetRowDataUrl`) | Single brand-fund sheet, SKU rows | **READ** (method to confirm) |
| GET | `/api/attributes/v1/brands-fund/cities/` (`brandFundCitiesURL`) | Cities available for a brand-fund sheet | **READ** |
| GET | `/api/bundlesandcombos/v1/bundles_and_combos_approval/brand-fund/` | Bundle/combo brand-fund approval data | **READ** (method to confirm) |
| POST | `/v1/report-requests/` (`REPORT_REQUEST_DATA`, body `{}`) | List the shared async report queue (READ despite POST) | **READ** (proven) |
| GET | `/v1/report-requests/download//{id}/` | Mint ~15-min presigned S3 URL for a completed report | **READ** (proven) |

**Out of scope — report-generation POSTs (enqueue a job / can fire an email; not pure reads):**
- `POST /v1/reports/bulk-invoice-excel/` (`BULK_DOWNLOAD`) — generate the Invoices Excel export.
- `POST /v1/reports/vendor-charges-excel/` (`VENDOR_CHARGEST_DOWNLOAD_URL`) — generate a Fees &
  Charges Excel.
- `POST /v1/reports/bulk-dn-download/` (`DN_BULK_DOWNLOAD`) — generate a Debit/Discrepancy-Note
  bulk export.
- `POST /v1/reports/bulk-prn-download/` (`PRN_BULK_DOWNLOAD`) — generate a Purchase-Return-Note
  bulk export.
  These mutate the report queue (and some trigger a "registered email"), so a **strict read-only
  CLI must not call them** — it should consume already-generated rows via `/v1/report-requests/`
  + `download//{id}/` instead (same pattern the [[Report-Requests]] / [[Sales]] / [[Stock-on-Hand]]
  flows use).

**Out of scope — true writes (never document as usable, never call):**
- **Raise a Dispute** on a Fees & Charges row — state-changing.
- **Brand-fund sheet upload** — `/api/attributes/v1/brands-sheets/` and the
  `bundleComboSheetUploadUrl` upload endpoint (submits new co-funding commitments).
- Any invoice **add / edit / delete** via PO-scheduling (`PO_SCHEDULING_ADD_INVOICE`,
  `PO_SCHEDULING_EDIT_INVOICE_DETAILS`, `PO_SCHEDULING_DELETE_INVOICE_CLICKED`).

## Real data seen (evidence)

- **Payment-state proof in bundle:** the invoice-detail component literally renders
  `payment_state === "PAID" ? "PAYMENT COMPLETED" : "PAYMENT PENDING"`, a **UTR number** slot, and
  a full deduction ladder (Invoice Amount → GRN Amount → Discrepancy → Approved → Deductions
  {Brand Fund, Price Variance} → Net Payable / `total_payout_amount`). This is the concrete money
  breakdown JIVO sees per invoice.
- **Live report queue** (2026-07-24 known-state, `/v1/report-requests/`, entity 1117): 20 reports,
  types = Invoices Excel, Bulk PO Excel, SOH Details Excel, Sales Details Excel — all `success`.
  Confirms the Payments-side bulk exports (Invoices Excel) land in the same queue this stack already
  reads. No dedicated "Charges"/"Payment Advice" report type has been observed in the queue yet
  (charges/advice are served by their **own direct GET/POST endpoints** above, not the queue).
- **Brand Fund is already pulled — but via email, not this API.** `blinkit-cli` (`brandfund pull`)
  fetches the Brand Fund CSV as an **IMAP attachment** from `tanuj@jivo.in`
  (`ecomcliauto/blinkit/VERIFIED-FINDINGS.md`, Flow 7: 1,920-row CSV with `brandfund_absolute_value`,
  `brandfund_percentage_value`, `total_brand_fund`, per date × city × item). The portal's native
  brand-fund **read** endpoints (`brands-fund/get/`, `get-sheet-rows/`, `-summary/view/`) are
  documented here for the first time and are **not yet wired into any CLI**.
- **No Payments/charges/UTR endpoint is in any current CLI.** `blinkit-cli` commands are `doctor`,
  `reports`, `sales pull`, `soh pull`, `brandfund pull`, `ads pull`; grep of `main.go` shows the
  only invoice/payment reference is the brand-fund email flow. Invoice-payment status, Fees &
  Charges, UTR, and Payment Advice are **documented-but-unbuilt**.
- **Request/response bodies uncaptured.** No `captures/partner/api/*.json` exists for any payment
  endpoint (only `profile-user.json` + `appointment-stats.json`), so exact filter keys and row
  schemas want a live (read-only) network capture to finalise — flagged inline above.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no report-generation POST, no dispute, no upload):

- `payments invoices [--status paid|upcoming|all|last_1_month] [--from --to]` — list invoice
  payment status via `POST /v2/invoice/` (`INVOICE_LISTS`). Pure READ.
- `payments invoice <vendorInvoiceId> <orderNumber>` — the payment breakdown (amounts, deductions,
  net payable, `payment_state`) via `POST /v1/invoice/details/`, with GRN line items from
  `POST /v1/invoice/grn-details/`. Pure READ.
- `payments utr <vendorInvoiceId>` — the bank UTR / settlement reference via `POST /v1/utr/invoices/`.
  Pure READ.
- `payments advice --from --to [--out FILE]` — download the Payment Advice ZIP via
  `GET /v1/vendor-reports/?…&download=zip`. Pure READ.
- `payments charges [--gran monthly|weekly|daily] [--from --to] [--status disputed|waived|pending]`
  — Fees & Charges list via `POST /v1/charges/`, plus `charges-summary/` + `charges-stats/` tiles
  and `charges/filters/` for filter values; `charges/{id}` for a single charge. Pure READ.
- `payments brandfund summary [--from --to]` / `payments brandfund sheet <sheetId>` — native
  brand-fund reads via `brands-fund-summary/view/`, `brands-fund/get/`, `brands-fund/get-sheet-rows/`,
  `brands-fund/cities/` (a portal-native alternative to the current IMAP `brandfund pull`). Pure READ.
- `payments aggregate --from --to` — headline payout totals via `POST /v1/aggregated-invoice-data/`.
  Pure READ.

Explicitly **excluded** from the read-only surface: triggering any `/v1/reports/…-download/` or
`…-excel/` generation, raising a dispute, uploading a brand-fund sheet, and any invoice
add/edit/delete — all writes / state-changing.

## Connections

- Portal shell & nav: [[Partner-Hub]] · index: [[00-Blinkit-Atlas]]
- **Tightest sibling** — invoices are grouped under `category:"payments"` and share the invoice
  detail page: [[Invoices]] (that note covers the GRN/discrepancy view; this note covers the
  payout/settlement view of the same invoices).
- Deductions on a payout trace back to promotional co-funding ([[Consumer-Offers]] brand fund) and
  to the ordering lane: [[PO-Summary]].
- Bulk Payments exports (Invoices Excel) ride the shared async queue: [[Report-Requests]] (same
  pattern as [[Sales]] · [[Stock-on-Hand]]).
- Charges/penalties can be linked to fulfilment/appointment performance: [[Appointments]] ·
  [[Score-Card]].
