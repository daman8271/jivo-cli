---
title: Partner Endpoints (read-only master index)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [blinkit, partner, endpoints]
---

# Partner Portal — Read-Only Endpoint Inventory

Consolidated endpoint spec for the Blinkit **Partner** portal (`partnersbiz.com/app`), grouped by section. This is the source of truth a future **read-only** CLI is generated from: everything in the READ tables is safe to expose; everything in the [Out of scope (writes)](#out-of-scope-writes) table mutates or side-effects and must **never** be wired into a read-only surface.

Hub: [[Partner-Hub]] · Atlas: [[00-Blinkit-Atlas]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]]

> ⚠️ READ-ONLY study. Contracts are reverse-read from the captured SPA JS bundles (`captures/partner/js/*`) — API-constant + `doHttpPost`/`doHttpGet` bindings — plus our own verified curl captures and `blinkit-cli`, **not** from any new live call. Rows marked *(to confirm)* have a binding but the method/path is not directly observed or not present in the captured bundle and needs a live network capture.

## Auth & base (from FACTS)

- **Host / base:** `https://www.partnersbiz.com` (`hostUrl.VendorConsoleEndpoint`).
- **Path prefixes seen:** `v1/`, `v2/`, `api/v1/`, `api/attributes/v1/`, `api/bundlesandcombos/v1/`, `vendor_appointment/api/v1/`, `vendor_appointment/api/v2/`.
- **Entity:** Jivo Wellness Pvt. Ltd. — `x-entity-id: 1117`, `x-entity-type: manufacturer`, internal `manufacturer_id: 176`.
- **Auth flow:** email-OTP → `access_token`/`refresh_token` (format `v2::<uuid>`). Unattended via `~/ecomcliauto/orchestrate/blinkit-login.sh` (reads OTP from `tanuj@jivo.in` via himalaya). ⚠️ `access_token` is **SHORT-LIVED** → refresh or re-login for long crawls.

**Required request headers (every data-API call):**

```http
token:         <access_token>          # v2::<uuid>
access_token:  <access_token>          # v2::<uuid>
x-api-key:     fe25a1da-...
x-entity-id:   1117
x-entity-type: manufacturer
service:       partnersbiz
app_client:    partnerbiz-web          # additional header seen in bundle captures
```

**Presigned S3 downloads** (`s3.ap-southeast-1.amazonaws.com/grofers.retail/partnersbiz/...`) need **no** portal headers — the minted URL is self-authenticating and expires ~15 min.

**Read/Write legend:** `READ` = pure JSON query · `READ (file)` = downloads a PDF/ZIP/CSV binary · `READ (async poll/download)` = polls the report queue then downloads a presigned file · `READ (to confirm)` = binding present, method/path not fully verified.

---

## Shared: async report queue — [[Report-Requests]]

The report queue is **cross-section**: [[Sales]], [[Stock-on-Hand]], [[Score-Card]], [[Invoices]], [[PO-Summary]] and [[Payments]] all *generate* a report (a side-effecting export — see out-of-scope table) then **poll + download** it through these three shared reads. This is the only end-to-end plain-curl-verified data path. Rows below marked "(async report queue)" refer back here rather than repeat them.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/v1/report-requests/` | List the async report queue, all types newest-first (a query despite POST; body `{}`) | READ |
| GET | `/v1/report-requests/download//{id}/` | Mint a presigned S3 download URL for a completed report (**literal double slash** is intentional; ~15 min expiry, re-mintable) | READ |
| GET | `<presigned S3 url>` | Download the finished CSV/XLSX (`s3.ap-southeast-1.amazonaws.com/grofers.retail/partnersbiz/…`), no portal auth | READ |

---

## [[PO-Summary]]

Inbound POs Blinkit raises to JIVO. SPA route `/app/po`; module `useFirebasePageTracking-CGSyAZ_Q.js`. Report-queue type: **"Bulk PO Excel"**.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/v1/client-po-details/` | PO list grid (`fetchPO`; body `{order_by,filters}`, params `{offset,limit}`, default `limit:30`, `order_by:"-expiry_date"`) | READ |
| GET | `/v1/client-po-details/distinct_values/city_name/` | City filter dropdown values | READ |
| GET | `/v1/client-po-details/distinct_values/facility_name/` | Facility filter dropdown values | READ |
| POST | `/v1/get-po-count/` | Aggregated summary card — PO count for current filters | READ (to confirm method) |
| POST | `/v1/get-po-amount/` | Aggregated summary card — total PO amount | READ (to confirm method) |
| GET | `/v1/get-po-details/?po_number={n}` | Single PO detail (detail page) | READ |
| POST | `/v1/client-po-items/{po_id}/` | Line items in a PO (params `paginate=false`) | READ |
| GET | `/v1/get-grn-details/` | GRN details for a PO | READ |
| GET | `/v1/partner_po_invoices/` | Invoices tied to a PO (PO Invoices tab) | READ |
| GET | `/v1/get-item-delivered-count/` | Delivered-item count per PO | READ |
| GET | `/v1/download-pod-pdf/?po_numbers={csv}` | POD PDFs (`purchase_orders[].pod_files`) | READ (file) |
| GET | `/v1/get-po-pdf-zip/` | Bulk PO PDF zip download | READ (file) |
| GET | `/v1/client-po-details/{id}/fetch_discrepancy_note_pdf/?vendor_invoice_id={n}` | Per-PO discrepancy note PDF | READ (file) |
| POST | `/v1/po-amendment/list/` | List existing PO amendments (read only) | READ |
| POST | `/v1/po-amendment/items/` | Items available for amendment (read only) | READ |
| GET/POST | `/v1/po-amendment/outlets-with-facility/` | Outlets-with-facility lookup for amendment | READ (to confirm method) |
| — | *(async report queue — Bulk PO Excel)* | Poll + download the generated Bulk PO Excel | READ (async poll/download → [[Report-Requests]]) |

---

## [[Invoices]]

JIVO's invoices against POs (GRN date, invoice excel). Report-queue type: **"Invoices Excel"** (delivered as `bulk_invoice_csv-{id}.csv`) — PROVEN live. Rides the shared queue + the [[Payments]] invoice endpoints; its own list/detail feed is not literal in the bundle.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/v1/report-requests/` | List queue; match the "Invoices Excel" row (shared queue) — PROVEN | READ |
| GET | `/v1/report-requests/download//{id}/` | Mint presigned S3 URL for a completed Invoices Excel — PROVEN | READ |
| GET | `<presigned S3 url>` | Download `bulk_invoice_csv-{id}.csv`, no auth — PROVEN | READ |
| GET | *invoice-summary list/detail feed* | On-screen invoice list/detail (not literal in bundle) | READ (to confirm) |
| GET | *per-invoice document links* | GRN / DN / scanned-invoice / ZIP links per invoice | READ (to confirm) |

---

## [[Report-Requests]]

The async report queue section itself. Canonical shared reads live in [Shared: async report queue](#shared-async-report-queue--report-requests) above; the bonus direct-JSON sales read below belongs to [[Sales]] but is exposed here for cross-check.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/v1/report-requests/` | List async report queue, all types newest-first (body `{}`) | READ |
| GET | `/v1/report-requests/download//{id}/` | Mint presigned S3 download URL (literal double slash) | READ |
| GET | `<presigned S3 url>` | Download finished CSV/XLSX, no portal auth | READ |
| POST | `/v1/get-sales-details/?offset=&limit=` | Bonus aggregate sales JSON (no date column; cross-check only) — see [[Sales]] | READ |

---

## [[Sales]]

Secondary sales / sell-out. Report-queue type: **"Sales Details Excel"**.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/v1/get-sales-details/?offset=&limit=` | Paginated on-screen sell-out grid (item × city units + MRP); body `{filters:{created_at__gte,created_at__lte},order_by:[]}`; aggregate with **no** date column — proven 200 | READ |
| — | *(async report queue — Sales Details Excel)* | Poll + download per-date Sales Details CSV | READ (async poll/download → [[Report-Requests]]) |

---

## [[Stock-on-Hand]]

Inventory (SOH) at Blinkit facilities. Report-queue type: **"SOH Details Excel"**.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/v1/get-entity-tabs/` | Gates whether the SOH tab renders for entity 1117 (401 → force-logout) | READ |
| — | *(async report queue — SOH Details Excel)* | Poll + download the SOH inventory snapshot CSV | READ (async poll/download → [[Report-Requests]]) |
| — | *SOH inline grid-populate feed* | Direct JSON that fills the on-screen `/app/soh` table — **not** in the captured bundle; no proven direct-JSON analogue to `get-sales-details` exists | READ (to confirm) |

---

## [[Score-Card]]

Performance metrics (fill rate, benchmarking, potential loss). Report-queue types: **"Scorecard Details Excel"** & **"Top 5 Potential Loss"** (filters `{start_date,end_date}`). Live-page module `ScoreCard-DK6XTVzq.js` was not captured, so the inline panel feeds are path-unknown.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/v1/report-requests/` | List queue; scorecard rows `type='Scorecard Details Excel'` / `'Top 5 Potential Loss'` (shared queue) — PROVEN | READ |
| GET | `/v1/report-requests/download//{id}/` | Presigned S3 download of a completed scorecard report — PROVEN *(section note wrote a single slash; canonical is the literal double slash)* | READ |
| GET/POST | `…/v1/…scorecard-summary…` | Summary panel data (exact path unknown) | READ (to confirm) |
| GET/POST | `…/v1/…fill-rate…` | Fill Rate metrics + summary (exact path unknown) | READ (to confirm) |
| GET/POST | `…/v1/…benchmark/ranking…` | Benchmarking & category ranking (exact path unknown) | READ (to confirm) |
| GET/POST | `…/v1/…potential-loss…` | Top-5 key-SKUs potential loss (exact path unknown) | READ (to confirm) |

---

## [[Consumer-Offers]]

Promotions / brand-funded offers (Brand Fund). Prefix `api/attributes/v1/` (single offers) and `api/bundlesandcombos/v1/` (bundle & combo offers).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/attributes/v1/brands-fund-summary/view/?manufacturer_id__in={id}` | Spends Summary cards (Total Spend + Unique Products) | READ |
| GET | `/api/attributes/v1/brands-fund-summary-count/view/?manufacturer_id__in={id}&to_user_email={email}&date__gte=&date__lte=` | Bulk Spends Summary export (delivers CSV **to email** — side-effect: emails the user) | READ (async export) |
| GET | `/api/attributes/v1/brands-fund/cities/?active=true&is_frontend=true` | City filter list | READ |
| GET | `/api/attributes/v1/brands-sheets/?offset=&limit=&manufacturer_id__in=&upload_source=BRAND&install_ts__gte=&install_ts__lte=&state__in=` | Offer Upload History list (single offers) | READ |
| GET | `/api/attributes/v1/brands-fund/get/?sheet_id=&row_number=&limit=` | Single offer sheet — row-wise detail | READ |
| GET | `/api/attributes/v1/brands-fund/get-sheet-rows/?sheet_id=` | Single offer sheet — row list | READ |
| GET | `/api/attributes/v1/brands-sheets/download-sample-file/?manufacturer_id__in=&id__in=` | Single-offer sample template | READ (file) |
| GET | `/api/bundlesandcombos/v1/bundles_and_combos_approval/brand-fund/?sheet_id=&row_number=&limit=` | Bundle offer sheet — row-wise detail | READ |
| GET | `/api/bundlesandcombos/v1/bundles_and_combos_approval/get-sheet-rows/?sheet_id=&limit=&offset=` | Bundle offer sheet — row list | READ |
| GET | `/api/bundlesandcombos/v1/bundles_and_combos_bf/download-sample-file/?bundle_type=` | Bundle sample template | READ (file) |
| GET | `/api/v1/bulk-upload-jobs/` | Bulk-upload job status list | READ |
| GET | `/api/bundlesandcombos/v1/bundles_and_combos_bf/` | Bundle upload-history list (query params to confirm) | READ |
| — | *month-end-claimable view feed* | Data source not in bundle | READ (to confirm) |

---

## [[Assortment]]

Listed / active SKUs per facility. Page is a lazy-loaded code-split chunk; the data feed is **not** in the captured bundle. No assortment/listing report type appears in the shared queue.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/v1/get-entity-tabs/` | Gates whether the Assortment tab renders for entity 1117 (401 → force-logout `invalid_entity_tab_401`) | READ |
| POST | `/v1/report-requests/` | Shared async report queue (no assortment-specific type observed) | READ |
| GET | `/v1/report-requests/download/{id}/` | Generic completed-report download by id | READ |
| — | *assortment data feed* | On-screen listing feed — not in bundle | READ (to confirm) |

---

## [[Payments]]

Invoice payments, UTR settlements, fees & charges, brand-fund summaries. Mix of `v1/`, `v2/`, and `api/attributes/v1/`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/v2/invoice/` | Invoice/payment list (`INVOICE_LISTS`) — tabs Paid / Upcoming / All / Last-1-Month | READ |
| POST | `/v1/invoices/` | Full invoice/payment feed (`INVOICE_DATA`) | READ |
| POST | `/v1/invoices-lite/` | Lite invoice feed (`INVOICE_DATA_LITE`) | READ |
| POST | `/v1/invoice/details/` | Payment breakdown — amounts / deductions / net_payable / payment_state (`INVOICE_DETAILS`) | READ |
| POST | `/v1/aggregated-invoice-data/` | Aggregated invoice/payment totals (`AGGREGATED_INVOICE_DATA`) | READ |
| POST | `/v1/invoice/grn-details/` | GRN line items behind an invoice (`INVOICE_ITEM_DETAILS`) | READ |
| POST | `/v1/utr/invoices/` | UTR / bank settlement reference per invoice (`INVOICE_UTR`) | READ |
| POST | `/vendor_appointment/api/v1/invoice/fetch-invoice/` | Invoices for POs (`FETCH_INVOICES_FOR_POS`) | READ |
| POST | `/v1/invoice/download/` | Single invoice PDF (`DOWNLOAD_INVOICE`) | READ (file) |
| GET | `/v1/vendor-reports/?start_date=&end_date=&download=zip` | Payment Advice remittance ZIP (`PAYMENT_ADVICE_DOWNLOAD`) | READ (file) |
| GET | `/v1/client-po-details/{poId}/grn/pdf/` | GRN report PDF (`GRN_REPORT_PDF`) | READ (file) |
| GET | `/v1/client-po-details/{poId}/fetch_discrepancy_note_pdf/` | Discrepancy/debit-note PDF (`DISCREPANCY_NOTE_PDF`) | READ (file) |
| POST | `/v1/charges/` | Fees & Charges list (`CHARGES_LIST_URL`) | READ |
| GET | `/v1/charges/{id}` | Single charge detail (`CHARGES_DETAIL_URL`) | READ |
| GET | `/v1/charges-summary/` | Fees & Charges summary tiles (`CHARGES_SUMMARY_URL`) | READ |
| GET | `/v1/charges-stats/` | Fees & Charges stat totals (`CHARGE_STATS_URL`) | READ |
| GET | `/v1/charges/filters/` | Charges filter options — facility/type/status (`CHARGES_FILTERS_URL`) | READ |
| GET | `/api/attributes/v1/brands-fund-summary/view/` | Daily brand-fund summary count (`dailySummaryCountUrl`) | READ |
| GET | `/api/attributes/v1/brands-fund-summary-count/view/` | Download daily summary (`downloadDailySummaryUrl`) | READ (to confirm method) |
| GET/POST | `/api/attributes/v1/brands-fund/get/` | Single sheet row-wise data (`singleSheetDataRowWiseurl`) | READ (to confirm method) |
| GET/POST | `/api/attributes/v1/brands-fund/get-sheet-rows/` | Single sheet row data (`singleSheetRowDataUrl`) | READ (to confirm method) |
| GET | `/api/attributes/v1/brands-fund/cities/` | Brand-fund city list (`brandFundCitiesURL`) | READ |
| GET/POST | `/api/bundlesandcombos/v1/bundles_and_combos_approval/brand-fund/` | Bundle brand-fund data | READ (to confirm method) |
| POST | `/v1/report-requests/` | Shared async report queue list (`REPORT_REQUEST_DATA`) — PROVEN | READ |
| GET | `/v1/report-requests/download//{id}/` | Presigned S3 report download — PROVEN | READ |

---

## [[Appointments]]

PO delivery scheduling (slots, courier, appointment passes). Prefix `vendor_appointment/api/v1/` and `.../v2/`.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/vendor_appointment/api/v1/appointment-stats/` | Pending / Upcoming / Fulfilled stat cards (`GET_APPOINTMENT_AGGREGATED_DATA`) | READ |
| POST | `/vendor_appointment/api/v1/appointments/` | Appointments list grid (POST carries filter body) (`GET_APPOINTMENTS`) | READ |
| GET | `/vendor_appointment/api/v1/appointments/fetch-cancel/` | Cancellability/count info — does NOT cancel (`APPOINTMENT_CANCELATION_COUNT`) | READ |
| GET | `/vendor_appointment/api/v1/courier-partner-details/` | Courier dropdown options (`FETCH_APPOINTMENT_COURIER_OPTIONS`) | READ |
| POST | `/vendor_appointment/api/v1/invoice/fetch-invoice/` | Invoices for POs (`FETCH_INVOICES_FOR_POS`) | READ |
| GET | `/vendor_appointment/api/v1/bulk-upload/sample-file` | Bulk-upload template (`DOWNLOAD_SAMPLE_BULK_UPLOAD_TEMPLATE`) | READ (file) |
| POST | `/vendor_appointment/api/v2/slots/available/` | Available delivery slots for PO(s) — inspect only (`GET_SLOTS_V2`) | READ |
| POST | `/vendor_appointment/api/v2/appointment/get-existing-appointments/` | Existing appointments for club/merge (`GET_EXISTING_APPOINTMENTS_V2`) | READ |
| GET | `/vendor_appointment/api/v2/appointment/clubbing-charges/` | Preview PO-clubbing/merge charges (`EXISTING_APPOINTMENT_ISSUE_DATE_DIFFERENT_V2`) | READ |
| GET | `/vendor_appointment/api/v2/appointment/` | Download appointment QR pass/letter (`DOWNLOAD_APPOINTMENT_QR`; method dispatched at runtime) | READ (file, to confirm) |

---

## [[EDI-Integration]]

Electronic data interchange setup. Prefix `/v1/vis/` + static docs.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/v1/vis/enabled-aggregators/` | List certified EDI partners/aggregators — Javis, B2BE, Unicommerce, Zoho (`INTEGRATION_PARTNERS_ENDPOINT`) | READ |
| GET | `/v1/sandbox/edi/yaml-doc` | EDI API OpenAPI/Swagger YAML spec (Scalar viewer at `/app/developers/documentation`) | READ |
| GET | `/ediStaticDoc.yaml` | Older/alternate static YAML spec for top-level `/developers` viewer (confirm which is live) | READ |
| — | *edi_lead_generation status* | `is_active` / `current_lead_status` (DRAFT/IN_PROGRESS/OAUTH_PENDING/COMPLETE) / aggregator — delivered via app-wide user/features bootstrap, not EDI-specific | READ (to confirm) |

---

## Out of scope (writes)

**Never expose these in a read-only CLI.** Two flavours: **mutations** (create / edit / cancel / upload / dispute — change business data or state) and **side-effecting exports** (`/v1/reports/*-excel/` and friends — they don't corrupt data but each creates a report-request row **and emails a copy to the account owner**, so they are not pure reads). Both are excluded from the read surface; poll + download the *already-generated* report via the shared [[Report-Requests]] queue instead.

| Section | METHOD | Path | Purpose | Type |
|---|---|---|---|---|
| [[PO-Summary]] | POST | `/v1/reports/bulk-po-excel/` | Generate Bulk PO Excel report (`REQUEST_BULK_PO_EXCEL`) | Side-effecting export |
| [[PO-Summary]] | POST | `/v1/po-amendment/process/` | Submit a PO amendment (`SUBMIT_PO_AMENDMENT_API_URL`) — edits ordered SKU/qty | WRITE |
| [[PO-Summary]] | POST | `/v1/client-po-details/asn-details/upsert/` | Upsert ASN / serial-code data (`POST_SERIAL_CODES_ENDPOINT`) | WRITE |
| [[PO-Summary]] | POST | `/v1/appointments/` · `/v1/appointments/fetch-cancel/` | PO scheduling / cancel (see [[Appointments]]) | WRITE |
| [[Invoices]] | POST | `/v1/reports/bulk-invoice-excel/` *(or `{invoice-bulk}-excel/`; exact path to confirm)* | Generate bulk invoice / GRN export | Side-effecting export |
| [[Invoices]] | POST | *PO-scheduling invoice add/edit/delete* | `PO_SCHEDULING_ADD/EDIT/DELETE_INVOICE` | WRITE |
| [[Report-Requests]] | POST | `/v1/reports/sales-details-excel/` | Generate Sales Details report job | Side-effecting export |
| [[Report-Requests]] | POST | `/v1/reports/soh-details-excel/` | Generate SOH inventory-snapshot report job | Side-effecting export |
| [[Report-Requests]] | POST | `/v1/reports/…` *(Invoices Excel / Bulk PO Excel generate rows)* | Report-generation endpoints not in bundle — confirm via live capture | Side-effecting export |
| [[Sales]] | POST | `/v1/reports/sales-details-excel/` | Generate per-date Sales Details CSV (creates report row + emails) | Side-effecting export |
| [[Stock-on-Hand]] | POST | `/v1/reports/soh-details-excel/` | Enqueue SOH export (body `{}` → `request_id`; emails a copy) | Side-effecting export |
| [[Score-Card]] | POST | `/v1/reports/scorecard-details-excel/` | Generate Scorecard Details Excel (name inferred from `…-excel/` pattern) | Side-effecting export |
| [[Score-Card]] | POST | `/v1/reports/…top-5-potential-loss…/` | Generate Top 5 Potential Loss export (exact path to confirm) | Side-effecting export |
| [[Consumer-Offers]] | POST (multipart) | `/api/attributes/v1/brands-sheets/` | Create/upload a single offer sheet | WRITE |
| [[Consumer-Offers]] | POST (multipart) | `/api/bundlesandcombos/v1/bundles_and_combos_bf/` | Create/upload a bundle & combo offer | WRITE |
| [[Assortment]] | — | *list / de-list / activate SKU action* | Not found in local material; must never be documented as usable | WRITE (unconfirmed) |
| [[Payments]] | POST | `/v1/reports/bulk-invoice-excel/` | Bulk invoice export (`BULK_DOWNLOAD`) | Side-effecting export |
| [[Payments]] | POST | `/v1/reports/vendor-charges-excel/` | Vendor charges export (`VENDOR_CHARGEST_DOWNLOAD_URL`) | Side-effecting export |
| [[Payments]] | POST | `/v1/reports/bulk-dn-download/` | Bulk debit/discrepancy-note export (`DN_BULK_DOWNLOAD`) | Side-effecting export |
| [[Payments]] | POST | `/v1/reports/bulk-prn-download/` | Bulk purchase-return-note export (`PRN_BULK_DOWNLOAD`) | Side-effecting export |
| [[Payments]] | POST | `/api/attributes/v1/brands-sheets/` + `bundleComboSheetUploadUrl` | Brand-fund sheet upload | WRITE |
| [[Payments]] | POST | *Raise a Dispute (Fees & Charges); invoice add/edit/delete via PO-scheduling* | Dispute / invoice mutation | WRITE |
| [[Appointments]] | POST | `/vendor_appointment/api/v2/appointments/create/` | Schedule appointment (`CREATE_APPOINTMENTS_V2`) | WRITE |
| [[Appointments]] | PUT | `/vendor_appointment/api/v2/appointments/` | Reschedule/edit (`UPDATE_APPOINTMENTS_V2`, `doHttpPut`) | WRITE |
| [[Appointments]] | POST | `/vendor_appointment/api/v2/appointments/cancel/` | Cancel appointment (`APPOINTMENT_CANCELATION_V2`) | WRITE |
| [[Appointments]] | — | `/vendor_appointment/api/v2/appointment/` | Release excess quantity (`RELEASE_EXCESS_QUANTITY_ENDPOINT`) | WRITE |
| [[Appointments]] | — | `/vendor_appointment/api/v2/appointment/` | Send appointment pass via WhatsApp/email (`SEND_APPOINTMENT_PASS`) | WRITE |
| [[Appointments]] | POST | `/vendor_appointment/api/v1/bulk-upload-request/` | Bulk upload appointments (`BULK_VARIANT_CREATION_UPLOAD`) | WRITE |
| [[Appointments]] | POST | `/vendor_appointment/api/v1/courier-partner/validate/` | Validate courier tracking number (`COURIER_PARTNER_TRACKING_NUMBER_VALIDATE_ENDPOINT`) | WRITE |
| [[Appointments]] | POST | `/vendor_appointment/api/v1/invoice/upload-s3-resource/` | Invoice-doc upload presign (`GET_PRESIGNED_URLS`) | WRITE-adjacent |
| [[EDI-Integration]] | GET | `/v1/vis/generate-url/?aggregator={name}` | Generate aggregator/OAuth authorization URL (`ZOHO_LEAD_GENERATION_ENDPOINT`, `generateOAuthLink`) — GET-shaped but **activation-only** | Activation (exclude) |
| [[EDI-Integration]] | POST | `/v1/client-requests/` | Submit EDI integration request/lead (`LEAD_GENERATION_ENDPOINT`, `doHttpPost`) | WRITE |

---

## Count
- **11 sections** documented ([[Partner-Hub]]).
- **~65 READ / read-flow contracts** catalogued above (incl. the 3 shared report-queue steps; Score-Card panel paths + the SOH / Assortment / Invoice inline feeds remain *to confirm*).
- **~22 WRITE / EXPORT endpoints** identified and held **out of scope**.
- Total ≈ **90 endpoint contracts** across the portal.

## Connections
- Hub & method: [[Partner-Hub]] · [[00-Blinkit-Atlas]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- Sections: [[PO-Summary]] · [[Invoices]] · [[Report-Requests]] · [[Sales]] · [[Stock-on-Hand]] · [[Score-Card]] · [[Consumer-Offers]] · [[Assortment]] · [[Payments]] · [[Appointments]] · [[EDI-Integration]]
