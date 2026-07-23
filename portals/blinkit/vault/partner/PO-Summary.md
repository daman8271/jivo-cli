---
title: PO Summary
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# PO Summary

The **Purchase Orders** section (SPA route `/app/po`, page-title enum `Jr.PO` = "Purchase Orders") lists every Purchase Order that **Blinkit raises to JIVO** (Jivo Wellness Pvt. Ltd., `x-entity-id=1117`, `x-entity-type=manufacturer`, internal `manufacturer_id=176`). It is the inbound-demand surface: each PO carries an ordered quantity/value, a delivery facility, an issue + expiry date, and a lifecycle status (Created → Unscheduled → Scheduled → Delivered/Fulfilled, or Cancelled/Expired). From here JIVO reviews POs, downloads them in bulk (Excel / PDF zip), drills into a single PO's items + invoices + GRN, and hands a PO into the appointment-scheduling flow. All calls hit `hostUrl.VendorConsoleEndpoint` (= `https://www.partnersbiz.com`) under the `v1/` prefix, using the header-token auth documented in the atlas. Endpoint contracts below were extracted from the code-split chunk `captures/partner/js/useFirebasePageTracking-CGSyAZ_Q.js` (the PO/`Orders` page module); they are the API-constant + `doHttpPost`/`doHttpGet` bindings, not live captures unless noted.

## Subpages & tabs

**List page** — `/app/po`
- The PO grid (server-paginated, default `limit:30`, `order_by:"-expiry_date"`).
- Aggregated summary cards driven by `get-po-count` + `get-po-amount` (event `PO_SUMMARY_AGGREGATED_FILTER_CLICKED`).
- **Group by** control (event `PO_SUMMARY_GROUP_BY_CHANGED`; grid also supports `groupByDate`).
- **Quick filters** (`PO_SUMMARY_QUICK_FILTER_APPLIED` / `_RESET_CLICKED`) and full **Table filters** (`PO_SUMMARY_TABLE_FILTERS_CLICKED` / `_APPLIED` / `_CLEARED`), plus removable global filter tags.
- **Bulk download** modal (`PO_SUMMARY_BULK_DOWNLOAD_MODAL_OPENED` / `_REQUESTED`) → Bulk PO Excel (async report) or Bulk PO PDF zip.
- Page-view event `PO_SUMMARY_VIEWED`.

**Detail page** — `/app/po-details/:poNumber` (page-title "PO Details"), tabbed:
- **PO Summary tab** (`PO_SUMMARY_TAB_CLICKED`) — the `PoDetailsSummary` card: Facility Name, Placed (`po_issue_date`), Date of expiry (`po_expiry_date`), Source (`vendor_name`), PO Manager (`pm_details.name` / email / phone), Delivery Facility Address; plus the PO's appointment list.
- **PO Items tab** (`PO_ITEMS_TAB_CLICKED`) — line items of the PO.
- **PO Invoices tab** (`PO_INVOICES_TAB_CLICKED`) — invoices raised against the PO.
- Per-PO downloads: PDF (`PO_DOWNLOAD_PDF_CLICKED`), Excel (`PO_DOWNLOAD_EXCEL_CLICKED`), GRN Report (`PO_DOWNLOAD_GRN_REPORT_CLICKED`), POD (`PO_DOWNLOAD_POD_CLICKED`).
- **PO Amendment** flow (edit ordered SKU/qty, apply to multiple POs, bulk update) — mutating; see out-of-scope note.
- **PO Scheduling** entry (Add PO → choose slot → schedule/reschedule/cancel, courier details, appointment QR/letter via email/WhatsApp) — mutating; lives under [[Appointments]]; see out-of-scope note.

## Filters & columns (what the table shows)

**Filters** (`FilterNames` enum → query keys, with `filterPlaceholders`):
| UI label | Query key | Values / source |
|---|---|---|
| City | `city_name` | distinct list from `client-po-details/distinct_values/city_name/` |
| Facility | `facility_name` | distinct list from `client-po-details/distinct_values/facility_name/` |
| Status | `po_state` | see status set below |
| PO Number | `po_number` | free-text search |
| Vendor Name | `vendor_name` | free-text search |

**Status set** (`AvailableStatuses`): Created · Cancelled · Expired · Fulfilled · Cancelled post Creation · Scheduled · Unscheduled · Rescheduled · Delivered · Partially Scheduled.
Quick-filter groupings: `OpenStatuses` = [Created, Unscheduled, Partially Scheduled]; `ScheduledStatuses` = [Scheduled, Rescheduled, Partially Scheduled]. (Rescheduled/Scheduled/Partially Scheduled collapse to a single "SCHEDULED" bucket when calling the appointment API.)

**List request shape** (`fetchPO`): `POST client-po-details/` body `{order_by, filters:{ po_number__in, po_state__in, facility_name…, city_name…, vendor_name… }}`, query params `{offset, limit}`.

**Columns.** The main `/app/po` grid renders PO-level fields — from the code + known captures: **PO Number, Order/Issue Date, PO Qty, PO Value, Status (`po_state`), Facility** (exact main-grid column array uses custom render cells; treat this set as confirmed-by-capture, full ordering to verify via live grid). The PO-picker grid used inside the scheduling modal is explicitly defined as: **PO No.** (`po_mappings[0].po_number`) · **Delivery Type** (`is_courier_unloading` → "Courier Vendor" / "Self") · **Issue Date** (`issue_date`) · **Total Quantity** (`total_units_ordered`) · **Total SKUs** (`item_count_ordered`) · **PO Expiry Date** (`expiry_date`). The detail "PO Summary" card fields are listed under Subpages above.

## API endpoints

Base = `https://www.partnersbiz.com/` + path. `doHttpPost`/`doHttpGet` = confirmed in the bundle; "to confirm" = binding present but method not directly observed.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `v1/client-po-details/` | PO list grid — `fetchPO`, body `{order_by,filters}`, params `{offset,limit}` | READ |
| GET | `v1/client-po-details/distinct_values/city_name/` | City filter dropdown values | READ |
| GET | `v1/client-po-details/distinct_values/facility_name/` | Facility filter dropdown values | READ |
| POST | `v1/get-po-count/` | Aggregated summary card: PO count for current filters (`FETCH_PO_COUNT`; method to confirm, likely POST w/ filters) | READ |
| POST | `v1/get-po-amount/` | Aggregated summary card: total PO amount (`FETCH_PO_AMOUNT`; method to confirm) | READ |
| GET | `v1/get-po-details/?po_number=<n>` | Single PO detail (detail page) — `doHttpGet` | READ |
| POST | `v1/client-po-items/<po_id>/` | Items in a PO (PO Items tab) — `doHttpPost`, params `paginate=false` | READ |
| GET | `v1/get-grn-details/` | GRN details for a PO (`FETCH_GRN_DETAILS`) | READ |
| GET | `v1/partner_po_invoices/` | Invoices tied to a PO (PO Invoices tab) / serialized items | READ |
| GET | `v1/get-item-delivered-count/` | Delivered-item count per PO | READ |
| GET | `v1/download-pod-pdf/?po_numbers=<csv>` | POD PDFs → `purchase_orders[].pod_files` — `doHttpGet` | READ (file) |
| GET | `v1/get-po-pdf-zip/` | Bulk PO PDF zip download (`FETCH_BULK_PO_PDF`) | READ (file) |
| GET | `v1/client-po-details/<id>/fetch_discrepancy_note_pdf/?vendor_invoice_id=<n>` | Per-PO discrepancy note PDF — `doHttpGet` | READ (file) |
| POST | `v1/reports/bulk-po-excel/` | Generate **Bulk PO Excel** async report (`REQUEST_BULK_PO_EXCEL`) → lands in report queue | READ-flow (async export; enqueues a report request) |
| POST | `v1/report-requests/` | Poll shared report queue (match the Bulk PO Excel row) | READ |
| GET | `v1/report-requests/download//<id>/` | Download completed Bulk PO Excel (presigned S3, ~15 min) | READ |
| POST | `v1/po-amendment/list/` | List existing PO amendments | READ |
| POST | `v1/po-amendment/items/` | Items available for amendment | READ |
| GET/POST | `v1/po-amendment/outlets-with-facility/` | Outlets-with-facility lookup for amendment (method to confirm) | READ |

**Out of scope (writes) — never expose in a read-only CLI:**
- `POST v1/po-amendment/process/` — **submit** a PO amendment (`SUBMIT_PO_AMENDMENT_API_URL`; edits ordered SKU/qty, bulk-update across POs). WRITE.
- `POST v1/client-po-details/asn-details/upsert/` — **upsert** ASN / serial-code data for a PO (`POST_SERIAL_CODES_ENDPOINT`). WRITE.
- Appointment scheduling verbs reached from PO scheduling — schedule / reschedule / cancel a PO's appointment, send appointment letter via email or WhatsApp (`v1/appointments/…`, `v1/appointments/fetch-cancel/`). WRITE; documented under [[Appointments]].

## Real data seen (evidence)
- **Report queue** (live, per project VERIFIED-FINDINGS): the shared `report-requests` queue returns rows of type **"Bulk PO Excel"** in `state:"success"` alongside Sales/SOH/Invoices — direct proof the Bulk PO Excel generate → poll → download path is live for entity 1117.
- **Auth/base** confirmed live: `https://www.partnersbiz.com` + `v1/`, header tokens (`token`+`access_token` `v2::<uuid>`, `x-api-key fe25a1da-…`, `x-entity-id 1117`, `x-entity-type manufacturer`), `manufacturer_id 176` embedded in report filters. See `ecomcliauto/blinkit/VERIFIED-FINDINGS.md`.
- **Endpoint set** extracted from `captures/partner/js/useFirebasePageTracking-CGSyAZ_Q.js` (PO/`Orders` module) — constants + `doHttpPost/doHttpGet` bindings, `FilterNames`, `AvailableStatuses`, `filterPlaceholders`, and the `PoDetailsSummary` card fields.
- **Screenshot** `captures/partner/sec-01-po-summary.png` shows only the PartnersBiz **login / "Request OTP"** page (session not authenticated at capture time) — the logged-in PO grid was **not** captured; a live authenticated grid + a sample `client-po-details` response body remain **to confirm via live network capture**.

## What a READ-ONLY CLI would expose (candidate commands)
- `blinkit po list [--status … --facility … --city … --vendor … --po-number … --limit 30 --offset 0 --order-by -expiry_date]` → `POST client-po-details/`.
- `blinkit po count` / `blinkit po amount` (same filters) → aggregated summary cards.
- `blinkit po facets cities` / `blinkit po facets facilities` → `distinct_values/{city_name,facility_name}/`.
- `blinkit po get <po_number>` → `get-po-details/`.
- `blinkit po items <po_id>` → `client-po-items/<po_id>/`.
- `blinkit po grn <po_number>` → `get-grn-details/`; `blinkit po invoices <po_number>` → `partner_po_invoices/`.
- `blinkit po pod <po_numbers>` → `download-pod-pdf/` (saves PDFs); `blinkit po pdf <po_numbers>` → `get-po-pdf-zip/` (saves zip).
- `blinkit po discrepancy <po_id> --invoice <vendor_invoice_id>` → `fetch_discrepancy_note_pdf/`.
- `blinkit po bulk-excel --from … --to …` → generate `reports/bulk-po-excel/` then poll `report-requests/` and download (read-flow export; mirrors the proven Sales/SOH chain).
- (Amendment **reads** only — list/items — could be surfaced read-only; `process` and `asn-details/upsert` must be excluded.)

## Connections
- Portal shell: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Feeds / adjacent: PO → invoice reconciliation in [[Invoices]]; Bulk PO Excel export lands in [[Report-Requests]]; PO scheduling & appointment letters in [[Appointments]]; catalog it references in [[Assortment]]; fulfilment SLAs surface in [[Score-Card]].
