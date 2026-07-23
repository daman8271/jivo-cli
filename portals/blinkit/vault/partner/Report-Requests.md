---
title: Report Requests
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: studied
---

# Report Requests

The **async report queue** of the Blinkit partner portal (route `/app/report-requests`,
SPA page `REPORT_REQUEST` / label "Report Request", analytics event `REPORT_REQUESTS_VIEWED`).
It is the portal's export centre: heavy exports (Sales, SOH, Invoices, PO) are not returned
inline — the portal enqueues a **report-request job**, the backend generates the file
asynchronously (~10-15s) and also emails it, and this page shows the resulting queue of jobs
so the user can watch them turn to *success* and download the finished file. Every export
elsewhere in the portal ([[Sales]], [[Stock-on-Hand]], [[Invoices]], [[PO-Summary]]) lands
here as a row. For our purposes it is the single most important section: the proven,
plain-curl-replayable pull chain for JIVO's Blinkit secondary-sales and inventory data all
runs through this queue. Entity is **`x-entity-id: 1117` (Jivo Wellness Pvt. Ltd., manufacturer)**;
the report filters carry the internal **`manufacturer_id: 176`**.

## Subpages & tabs

- **Single page, no sub-tabs.** The route resolves to one table view (`REPORT_REQUEST`).
  There is no per-type tab in the bundle — the queue is a **single shared list across all
  report types** (Sales, SOH, Invoices, Bulk PO). You disambiguate a row by its `type` field,
  its `filters`, or its `id`.
- Generate actions live on the *source* pages (a "Generate"/export button on [[Sales]],
  [[Stock-on-Hand]], etc.), not on this page; this page is where the finished job appears and
  is downloaded.

## Filters & columns (what the table shows)

The table is an antd generic table rendered from the `POST /v1/report-requests/` response
rows; the bundle does not carry literal column-header strings (generic table + server-driven
labels), so exact header text is **to confirm via live screenshot / network capture**. From
the proven row schema and the status labels found in the bundle (`success`, `failed`,
`processing`, `Completed`, `Success`), the table is built from these fields:

| Shown as (inferred) | Source field | Notes |
|---|---|---|
| Report Type | `type` | e.g. `Sales Details Excel`, `SOH Details Excel`, `Invoices Excel`, `Bulk PO Excel` |
| Status | `state` | `processing` → `success` (or `failed`); UI shows "Completed"/"Success" |
| Requested / Created | `created_at` | when the job was enqueued |
| Updated | `updated_at` | when it finished |
| Date range (filters) | `comments.filters.created_at__gte` / `__lte` | the window the report covers; `manufacturer_id__in:[176]` |
| File | `comments.file_path` | e.g. `sales_csv-<id>.csv` |
| Download (action) | derived from `id` | button → mints a presigned S3 URL (see endpoints) |
| (hidden) email log | `comments.email_logs` | `{subject, success, recipients}` — the report is also emailed |

- **Filters:** the queue list itself is fetched with an empty body `{}` (no client-side filter
  params were observed) — it returns the recent queue newest-first. The *date-window* filter
  (`created_at__gte`/`__lte`) is an attribute of the report **generate** call, not of the list.

## API endpoints

Base `https://www.partnersbiz.com`, prefix `/v1/`. Auth = header tokens
(`token` + `access_token` = `v2::<uuid>`, `x-api-key: fe25a1da-…`, `x-entity-id: 1117`,
`x-entity-type: manufacturer`, `service: partnersbiz`, `app_client: partnerbiz-web`).
Endpoints confirmed from `ecomcliauto/clis/blinkit-cli/client.go` + live captures in
`ecomcliauto/captures/blinkit/`.

| METHOD | Path | Purpose | Read / Write |
|---|---|---|---|
| POST | `/v1/report-requests/` (body `{}`) | List the report-request **queue** (all types, newest first). Despite POST, it is a pure query. | **READ** |
| GET | `/v1/report-requests/download//{id}/` | Mint a **presigned S3 download URL** for an already-completed report `id` (note the literal double slash — that is how the SPA builds it, and it works). ~15 min expiry, re-mintable. | **READ** |
| GET | `<presigned S3 url>` (`s3.ap-southeast-1.amazonaws.com/grofers.retail/partnersbiz/…`) | Download the finished CSV/XLSX. No portal auth needed (URL is presigned). | **READ** |
| POST | `/v1/get-sales-details/?offset=&limit=` (body `{"filters":{created_at__gte,__lte},"order_by":[]}`) | Bonus direct aggregate sales JSON (NOT via the queue; no `date` column — aggregate view, health/cross-check only). | **READ** |
| POST | `/v1/reports/sales-details-excel/` (body `{"filters":{created_at__gte,__lte}}`) | **Generate** a Sales Details report job (enqueues + emails). Creates a resource → treat as a write. | **WRITE — OUT-OF-SCOPE** |
| POST | `/v1/reports/soh-details-excel/` (body `{}`) | **Generate** an SOH (inventory snapshot) report job. Creates a resource → treat as a write. | **WRITE — OUT-OF-SCOPE** |

Out-of-scope (writes) note: the two `/v1/reports/*-excel/` endpoints are how the portal
*creates* new report jobs. Under the read-only rule they are documented for completeness only
and must NEVER be called from a read-only CLI — they enqueue work and trigger emails. The
`Invoices Excel` and `Bulk PO Excel` rows seen in the live queue are generated by their own
(unconfirmed) `/v1/reports/…` generate endpoints from the [[Invoices]] / [[PO-Summary]] pages —
**those generate endpoints are to confirm via live network capture**, and are equally
out-of-scope as writes.

## Real data seen (evidence)

- **Live queue (`POST /v1/report-requests/`):** 20 reports returned, `type` ∈ {Invoices Excel,
  Bulk PO Excel, SOH Details Excel, Sales Details Excel}, all `state = success`.
- **Full read chain verified end-to-end (2026-07-08, plain curl, Mac Air):**
  poll `POST /v1/report-requests/` → `GET /v1/report-requests/download//2693589/`
  → presigned S3 `GET` → a real **1,838-row Sales CSV** (248 KB, `binary/octet-stream`).
  Sales CSV schema: `item_id, item_name, manufacturer_id, manufacturer_name, city_id,
  city_name, category, date, qty_sold, mrp` (per item × city × **date**, real daily grain).
- **SOH chain verified:** report `#2693601` → **329-row** SOH CSV, schema
  `created_at, backend_facility_name, backend_facility_id, item_id, item_name,
  backend_inv_qty, frontend_inv_qty`.
- Row `comments` block carries `filters` (`created_at__gte/__lte`, `manufacturer_id__in:[176]`),
  `file_path` (`sales_csv-<id>.csv`), and `email_logs` (report also emailed to `tanuj@jivo.in`,
  subject `Sales Detail Report <from> - <to>` — an IMAP fallback if the API ever breaks).
- Bundle confirms the wiring only: `report-requests` → `Jr.REPORT_REQUEST` ("Report Request")
  route mapping + `REPORT_REQUESTS_VIEWED` analytics event; status labels `success` / `failed`
  / `processing` / `Completed`. The API endpoint literals are **not** in `index.js` (built at
  runtime / server-driven) — they are proven from the captures and the Go client instead.

## What a READ-ONLY CLI would expose (candidate commands)

The whole read surface is: *list the queue* and *download reports that already exist*. No
generation.

- `reports list [--json]` — `POST /v1/report-requests/` body `{}`; print the queue
  (id, type, state, created_at, date-range, file_path). Mirrors blinkit-cli's `reports`.
- `reports get <id> --out <file>` — `GET /v1/report-requests/download//<id>/` → mint the
  presigned URL → plain `GET` → save the finished CSV/XLSX. Read-only: only fetches reports
  that are **already** `state = success`; never generates.
- `reports url <id>` — just print the freshly-minted presigned S3 download URL (no fetch).
- `sales aggregate --from --to [--json]` — `POST /v1/get-sales-details/` for the fast
  aggregate cross-check (no `date` column; verification only, not the upload source).
- **Explicitly NOT exposed:** any `generate`/`pull` that hits `/v1/reports/*-excel/` — those
  are writes and are out of scope for the read-only tool. (The existing `blinkit-cli sales
  pull` / `soh pull` do generate+poll+download; a read-only variant keeps only the poll+download
  half against pre-existing rows.)

## Connections

- Portal home: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Consumes/produces exports for: [[Sales]] (Sales Details Excel), [[Stock-on-Hand]]
  (SOH Details Excel), [[Invoices]] (Invoices Excel), [[PO-Summary]] (Bulk PO Excel)
- Related sections: [[Score-Card]] · [[Assortment]] · [[Payments]] · [[Appointments]]
  · [[Consumer-Offers]] · [[EDI-Integration]]
