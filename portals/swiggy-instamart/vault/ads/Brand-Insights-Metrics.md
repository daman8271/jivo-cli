---
title: Brand Insights Metrics
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Brand Insights Metrics

> Ad performance metrics: impressions, clicks, spend, ROAS, share-of-voice.

**Brand Insights** is the advertiser-metrics engine behind the ads dashboards.
`advertiser/metrics` and `advertiser/metrics/batch` accept a metric list, a
dimension grouping and a filter set, and return time-series or grouped
performance. `get-advertiser-metrics` is the uptime/efficiency variant.

The metric vocabulary reachable here is far wider than sales: impressions,
clicks, CTR, CVR, conversions, spend, budget burnt (including realtime), ROAS,
ROI, CPO, eCPS, AOV, reach, sessions, new-user counts, market share, and three
share-of-voice metrics (`SOV`, `OVERALL_SHARE_OF_VOICE`,
`SPONSORED_SHARE_OF_VOICE`) plus benchmark CTR/CVR/ROI to compare against
category norms.

**Endpoints in this section:** 6 (4 read, 1 write/export, 1 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics` | `BRAND_INSIGHTS_METRICS` | **PROVEN LIVE 200** | call site .post() on BRAND_INSIGHTS_METRICS | live: ['POST'] -> [200], 6884B |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/batch` | `BRAND_INSIGHTS_GET_BATCH_ADVERTISER_METRICS` | **PROVEN LIVE 200** | call site .post() on BRAND_INSIGHTS_GET_BATCH_ADVERTISER_METRICS | live: ['POST'] -> [200], 4049B |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/report/list` | `LIST_CUSTOM_REPORTS` | **PROVEN LIVE 200** | call site .post() on LIST_CUSTOM_REPORTS | live: ['POST'] -> [200], 15039B |
| READ | POST | `partner-api.swiggy.com/instamart/v1/metrics` | `METRICS` | documented (not observed live) | call site .post() on METRICS |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/api/v1/advertiser/metrics/report` | `INITIATE_CUSTOM_METRICS_REPORT` | EXPORT — call site .post() on INITIATE_CUSTOM_METRICS_REPORT |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/get-advertiser-metrics` | `UPTIME_METRICS` | read-shaped path but METHOD UNRESOLVED — denied per G1 |

## Gotchas

- `/api/v1/3p/advertiser/metrics/batch` (the brandverse third-party variant)
  returned **HTTP 403** on passive render for this account — PROVEN to exist,
  PROVEN to be denied to `ecom1@jivo.in`. Recorded as role-denied, not guessed.
- `BENCHMARK_*` metrics are Swiggy's category benchmark, i.e. competitor-relative
  performance without naming competitors. Nothing in JIVO's stack reads them.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-26-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-26-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png)
- `sec-46-instamart-bdpo-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-46-instamart-bdpo-Jivo-Wellness-.png)
- `sec-66-instamart-bdpo-Jivo-.png`

  ![screenshot](../captures/walk2/sec-66-instamart-bdpo-Jivo-.png)
- `d21-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d21-instamart-bdpo-Jivo-Mart-Pvt-Ltd-.png)
- `d40-instamart-bdpo-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d40-instamart-bdpo-Jivo-Wellness-.png)
- `d59-instamart-bdpo-Jivo-.png`

  ![screenshot](../captures/walk4/d59-instamart-bdpo-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
