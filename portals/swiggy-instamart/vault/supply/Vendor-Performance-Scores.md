---
title: Vendor Performance Scores
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Vendor Performance Scores

> Swiggy's scorecard on JIVO's supplying vendors.

**PERFORMANCE** is the first block in the Supply Portal nav and has three views:
`Vendor Scores` (`/im-vendor/performance-vendor-scores`), `Facility Level`
(`/im-vendor/performance-facility-view`) and `Item Level`
(`/im-vendor/performance-item-list-view`). All three are served by
`searchSupplierPerformanceMetrics` with a different grouping.

This is Swiggy's own scorecard on how well JIVO's distributors serve it — fill
rate, appointment adherence, short supply. It is the surface most likely to be
quoted back at JIVO in a commercial conversation, and JIVO does not read it.

**Endpoints in this section:** 1 (1 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `picker.swiggy.com/api/v1/searchSupplierPerformanceMetrics` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 77B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- One endpoint, three groupings — the view is chosen by the request body, not
  the path, so the three routes share a single endpoint row.
- Vendor-scoped; pick the vendor before quoting a score.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-16-im-vendor-performance-vendor-scores.png`

  ![screenshot](../captures/walk1/sec-16-im-vendor-performance-vendor-scores.png)
- `sec-17-im-vendor-performance-item-list-view.png`

  ![screenshot](../captures/walk1/sec-17-im-vendor-performance-item-list-view.png)
- `sec-18-im-vendor-performance-facility-view.png`

  ![screenshot](../captures/walk1/sec-18-im-vendor-performance-facility-view.png)
- `sec-15-im-vendor-performance-vendor-scores.png`

  ![screenshot](../captures/walk2/sec-15-im-vendor-performance-vendor-scores.png)
- `sec-16-im-vendor-performance-item-list-view.png`

  ![screenshot](../captures/walk2/sec-16-im-vendor-performance-item-list-view.png)
- `sec-17-im-vendor-performance-facility-view.png`

  ![screenshot](../captures/walk2/sec-17-im-vendor-performance-facility-view.png)
- `flt-10-im-vendor-performance-vendor-scores-a-default.png`

  ![screenshot](../captures/walk3/flt-10-im-vendor-performance-vendor-scores-a-default.png)
- `flt-11-im-vendor-performance-item-list-view-a-default.png`

  ![screenshot](../captures/walk3/flt-11-im-vendor-performance-item-list-view-a-default.png)
- `flt-12-im-vendor-performance-facility-view-a-default.png`

  ![screenshot](../captures/walk3/flt-12-im-vendor-performance-facility-view-a-default.png)
- `d12-im-vendor-performance-item-list-view.png`

  ![screenshot](../captures/walk4/d12-im-vendor-performance-item-list-view.png)
- `d13-im-vendor-performance-facility-view.png`

  ![screenshot](../captures/walk4/d13-im-vendor-performance-facility-view.png)
- `v07-im-vendor-performance-vendor-scores.png`

  ![screenshot](../captures/walk5/v07-im-vendor-performance-vendor-scores.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
