---
title: Vendor Reports Queue
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, vendor-reports]
status: studied
---

# Vendor Reports Queue

The **Vendor Reports Queue** is Zepto's single **async report inbox** — the shared queue where every
tabular export JIVO (Jivo Wellness Pvt. Ltd., Manufacturer, STANDARD tier, `manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`) requests across the portal lands, tracks its generation
status, and is finally downloaded as a file. It is the sink, not a data source: a section (Sales,
Inventory/Stock, Ads reporting, etc.) fires a **generate** request with a `reportType` +
`reportPayload`; Zepto builds the file asynchronously; a row appears here with a status; when it is
ready the row exposes a **download** link (presigned). The queue is served entirely by
`fcc.zepto.co.in` under the `api/v1/reports*` prefix, using the single Zepto JWT (header
`authorization: <jwt>`, **no** `Bearer` prefix) that works across all Zepto backends. The endpoint
contracts below were read out of the vendor micro-frontend bundle (remote `vendor(635)`, chunks
`1183.8940422c8268d8dc.js` + `3539.64ab07c46b8741b5.js`) as the API-constant map
`L={GET_REPORTS_LISTING, REQUEST_DOWNLOAD_REPORT, downloadReports, retryReports}`, and are
cross-confirmed by the existing vendor captures under `captures/vendor/` (the exact list/request/
download curls the running SPA fired).

## Scope note — this is where the existing zepto-cli pulls already live

Two of this section's endpoints are **already in production use** by `zepto-cli`: the 6 documented
pull flows (SALES + INVENTORY reports, and the ads 2×2 products/brands × range/daily exports) all
(a) POST a generate request to `api/v1/reports/request`, then (b) poll `api/v1/reports` (this
queue's listing), then (c) pull the file from `api/v1/reports/{id}/download`. So the **listing** and
**download** legs are the read surface of this section; the **generate** (`/request`) and **retry**
legs are the write/export surface and are held strictly out of scope for a read-only CLI. The
captured curls in `captures/vendor/23-sales-list.txt`, `23-sales-request.txt`, `23-sales-download.txt`
are the ground-truth wiring.

## SPA routes

This section is reached under both the vendor-shell report routes and the ads-shell reporting routes
(the ads reporting overview/insight pages funnel their exports into the same `fcc` report queue):

- `/vendor/reports`
- `/reports`
- `/report`
- `/ads/reports`
- `/ads/reporting`
- `/ads/reporting/overview`
- `/ads/reporting/live-insights`
- `/ads/reporting/campaign-review`
- `/ads/reporting/campaign-review/details`
- `/ads/reporting/users`

## Backend host

- `fcc.zepto.co.in` — vendor reports (`api/v1/reports*`) and the ads-bff namespace
  (`ads-bff/api/v1/reports/uploads`). Single JWT auth; WAF headers (`waf-enabled`,
  `x-aws-waf-token`, `x-proxy-target: brand-analytics`) present in captures but **not enforced** as
  of the last verified capture.

## What the queue row shows

The listing is server-paginated (`?offset=&limit=`, e.g. the captured `offset=0&limit=13`). Each row
is a requested report carrying — from the generate payload and the download wiring — a **report type**
(`reportType`, e.g. `SALES`), the **date window** (`reportPayload.startDate` / `endDate`, ISO-8601
UTC), a generation **status**, a report **id** (UUID, e.g. `a936dc69-679f-4e8a-95f1-3ca802b01246`),
and, once ready, a **download** action that mints the file. Exact row schema (status enum, timestamps,
row count, file name) wants a live authenticated capture to lock down — the probe below could not,
because the captured token was expired at study time.

## API endpoints (reads)

Base = `https://fcc.zepto.co.in/` + path. Constants are from the bundle map
`L={GET_REPORTS_LISTING:"api/v1/reports", REQUEST_DOWNLOAD_REPORT:"api/v1/reports/request",
downloadReports:e=>`api/v1/reports/${e}/download`, retryReports:e=>`api/v1/reports/${e}/retry`}`.
"documented (not probed)" = wiring confirmed in bundle + capture curls, but not live-verified this
session (token expired → 401).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/v1/reports?offset=&limit=` | Reports queue listing — every requested report + status (`GET_REPORTS_LISTING`; the poll leg of the SALES/INVENTORY/ads pulls). Confirmed by `captures/vendor/23-sales-list.txt`. **documented (not probed)** — live GET returned `401 {"code":401,"message":"Token expired"}` this session. | READ |
| GET | `/api/v1/reports/{id}/download` | Download a completed report file for a queue row (`downloadReports`; mints/serves the generated file, presigned). Confirmed by `captures/vendor/23-sales-download.txt` (id `a936dc69-…`). No state change — read effect. | READ (file) |

## Out of scope (writes)

Never expose in a read-only CLI; documented from the bundle/captures only, never called.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `/api/v1/reports/request` | **Generate** a report — enqueues a new async job (`REQUEST_DOWNLOAD_REPORT` / `REQUEST_REPORT`). Capture `23-sales-request.txt` proves it is a POST with body `{"reportType":"SALES","reportPayload":{"startDate":…,"endDate":…}}`. Mutates the queue. | EXPORT (report-generation POST) |
| POST/PUT | `/api/v1/reports/{id}/retry` | **Retry** a failed report row (`retryReports`) — re-triggers generation for a queue row. Method not directly captured; state-changing. | WRITE |
| POST | `ads-bff/api/v1/reports/uploads` | Ads-bff report **uploads** endpoint (from `1183.8940422c8268d8dc.js`, alongside `file-job/get-signed-url` + `file-job/download-file` + `wallet/s3/presigned-url`). Upload = state-changing. | EXPORT (upload) |

## Real data seen (evidence)

- **Wiring is capture-confirmed, not invented.** `captures/vendor/23-sales-list.txt` is the exact
  `GET https://fcc.zepto.co.in/api/v1/reports?offset=0&limit=13` the SPA fired;
  `23-sales-download.txt` is `GET …/api/v1/reports/a936dc69-679f-4e8a-95f1-3ca802b01246/download`;
  `23-sales-request.txt` is the `POST …/api/v1/reports/request` generate call with the
  `{reportType:"SALES", reportPayload:{startDate,endDate}}` body. The bundle constant map matches
  these one-for-one.
- **Auth shape.** JWT in the `authorization` header with **no** `Bearer` prefix; identity in the
  token = `emailId ecom1@jivo.in`, `roleName "External Super Ads Admin"`, `category External`. The
  captured token's `exp` = `1783967399` (Mon Jul 13 2026), so it was **expired** at study time
  (2026-07-24). WAF headers present in the curl but the API answered without enforcing them in prior
  captures.
- **Probe result.** One read-only probe was attempted (`GET /api/v1/reports?offset=0&limit=5`); it
  returned `HTTP/2 401 {"code":401,"message":"Token expired"}`. Per the read-only guardrails the
  probe run stopped there — **0 endpoints upgraded to PROVEN**; all remain documented. Transcript:
  `captures/vendor/vendor-reports-probes.txt`. A fresh token would let the listing + download legs be
  verified live (both are already exercised by `zepto-cli`'s working SALES/INVENTORY pulls).

## What a READ-ONLY CLI would expose (candidate commands)

- `zepto reports list [--offset 0 --limit 30]` → `GET api/v1/reports` (poll the queue, show
  type/status/id/date-window per row). Pure READ.
- `zepto reports download <id> [--out FILE]` → `GET api/v1/reports/{id}/download` (save an
  already-generated file). Pure READ (file).

Explicitly **excluded** from the read-only surface: `POST api/v1/reports/request` (generate),
`api/v1/reports/{id}/retry` (retry), and `ads-bff/api/v1/reports/uploads` (upload) — all
state-changing. A strict read-only CLI must only **consume** rows already generated by the portal UI,
never enqueue or retry a job.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- **Feeders** — sections whose exports land in this queue: [[Stock-View-Inventory]] (INVENTORY
  reports), the Sales export flow, and the ads reporting pages ([[Brand-Analytics]] ·
  [[Ads-Campaigns-Booking-Keywords]]) reached via the `/ads/reporting/*` routes above.
- Sibling vendor-lane surfaces that also generate exports into this queue: [[Purchase-Orders]] ·
  [[Invoicing]] · [[Payments]].
