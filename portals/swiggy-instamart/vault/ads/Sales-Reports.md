---
title: Sales Reports
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Sales Reports

> The sales xlsx queue — the one surface JIVO's cron already uses.

**Sales** (`/instamart/sales`) is the only Swiggy surface JIVO's daily automation
touches. The contract is three steps: **generate** (`/api/v1/sales/report`,
enqueue), **poll/list** (`/api/v1/sales/reports`), **download** the
`downloadUrl`, which is a **presigned S3 link on
`im-brand-reports-in-west.s3.ap-south-1.amazonaws.com`** requiring no auth of its
own — the presign *is* the auth.

Live, the queue held **12 completed report rows** for Jivo Wellness, the newest
`IMSales_072926_1731` covering 2026-07-01 → 2026-07-28. The parallel
`/instamart/v1/report/*` family on `partner-api` is the newer report API with
`list-sales` and `list-bdpo` variants.

**Endpoints in this section:** 7 (4 read, 3 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/sales/reports` | `LIST_SALES_REPORTS` | **PROVEN LIVE 200** | call site .post() on LIST_SALES_REPORTS | live: ['POST'] -> [200], 8509B |
| READ | POST | `partner-api.swiggy.com/instamart/v1/report` | `GET_REPORT` | documented (not observed live) | call site .post() on GET_REPORT |
| READ | POST | `partner-api.swiggy.com/instamart/v1/report/list-bdpo` | `GET_BDPO_REPORT` | documented (not observed live) | call site .post() on GET_BDPO_REPORT |
| READ | POST | `partner-api.swiggy.com/instamart/v1/report/list-sales` | `GET_SALES_REPORT` | documented (not observed live) | call site .post() on GET_SALES_REPORT |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/api/v1/sales/report` | `INITIATE_SALES_METRIC_REPORT` | EXPORT — call site .post() on INITIATE_SALES_METRIC_REPORT |
| POST | `partner-api.swiggy.com/instamart/v1/report/initiate-bdpo-report` | `INITIATE_BDPO_METRIC_REPORT` | EXPORT — call site .post() on INITIATE_BDPO_METRIC_REPORT |
| UNKNOWN | `partner-api.swiggy.com/instamart/v1/report/initiate-sales-report` | `—` | EXPORT — report generation / enqueue — creates a row + burns queue budget (G2) |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- **Listing and downloading are reads; generating is a WRITE** (G2) — it creates
  a queue row and burns the account's report quota. The read-only CLI exposes
  list + download only.
- `reports.nextPageOffset` is an operation name, not an integer — the queue is
  paginated and 12 rows is one page, not the total.
- Report rows expire (24 h per one internal note, 7 days per a later and better
  tested one), which is why JIVO's cron must regenerate daily.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-23-instamart-sales-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-23-instamart-sales-Jivo-Mart-Pvt-Ltd-.png)
- `sec-24-instamart-sales-insights-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-24-instamart-sales-insights-Jivo-Mart-Pvt-Ltd-.png)
- `sec-25-instamart-reports-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-25-instamart-reports-Jivo-Mart-Pvt-Ltd-.png)
- `sec-43-instamart-sales-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-43-instamart-sales-Jivo-Wellness-.png)
- `sec-45-instamart-reports-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-45-instamart-reports-Jivo-Wellness-.png)
- `sec-63-instamart-sales-Jivo-.png`

  ![screenshot](../captures/walk2/sec-63-instamart-sales-Jivo-.png)
- `sec-65-instamart-reports-Jivo-.png`

  ![screenshot](../captures/walk2/sec-65-instamart-reports-Jivo-.png)
- `d18-instamart-sales-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d18-instamart-sales-Jivo-Mart-Pvt-Ltd-.png)
- `d19-instamart-sales-insights-Jivo-Mart-Pvt-Ltd--Category.png`

  ![screenshot](../captures/walk4/d19-instamart-sales-insights-Jivo-Mart-Pvt-Ltd--Category.png)
- `d20-instamart-reports-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d20-instamart-reports-Jivo-Mart-Pvt-Ltd-.png)
- `d37-instamart-sales-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d37-instamart-sales-Jivo-Wellness-.png)
- `d38-instamart-sales-insights-Jivo-Wellness--Category.png`

  ![screenshot](../captures/walk4/d38-instamart-sales-insights-Jivo-Wellness--Category.png)
- `d39-instamart-reports-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d39-instamart-reports-Jivo-Wellness-.png)
- `d56-instamart-sales-Jivo-.png`

  ![screenshot](../captures/walk4/d56-instamart-sales-Jivo-.png)
- `d57-instamart-sales-insights-Jivo--Category.png`

  ![screenshot](../captures/walk4/d57-instamart-sales-insights-Jivo--Category.png)
- `d58-instamart-reports-Jivo-.png`

  ![screenshot](../captures/walk4/d58-instamart-reports-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
