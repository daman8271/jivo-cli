---
title: Returns RTV and Purchase Returns
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Returns RTV and Purchase Returns

> Return-to-vendor and purchase-return flows.

Two adjacent return surfaces sit under **RETURNS** in the Supply Portal nav:

- **Return To Vendor** (`/im-vendor/rtv`) — stock Swiggy is sending back, header
  (`search/rtv`) and line (`search/rtvLines`) level.
- **Purchase Returns** (`/im-vendor/purchase-returns`) — the purchase-return
  documents, again header (`searchPurchaseReturns`) and line
  (`searchPurchaseReturnLines`) level, with `returnMetrics` for the summary
  tiles.

For an edible-oil brand these two are the direct read on damages, near-expiry
pullbacks and rejected consignments — a cost line JIVO currently has no
automated visibility into at all.

**Endpoints in this section:** 5 (5 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `picker.swiggy.com/api/v1/returnMetrics` | `—` | **PROVEN LIVE 400** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [400], 77B |
| READ | POST | `picker.swiggy.com/api/v1/search/rtv` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 101B |
| READ | POST | `picker.swiggy.com/api/v1/search/rtvLines` | `—` | documented (not observed live) | nearest client .post() after the template url |
| READ | POST | `picker.swiggy.com/api/v1/searchPurchaseReturnLines` | `—` | documented (not observed live) | nearest client .post() after the template url |
| READ | POST | `picker.swiggy.com/api/v1/searchPurchaseReturns` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 77B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- Both grids expose `total_records_count` and a `last_update_time`; quote those
  rather than on-screen rows.
- Nothing here is a write, but the pages sit next to PO Booking's booking
  controls — stay on the returns routes.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-12-im-vendor-rtv.png`

  ![screenshot](../captures/walk1/sec-12-im-vendor-rtv.png)
- `sec-13-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk1/sec-13-im-vendor-purchase-returns.png)
- `sec-11-im-vendor-rtv.png`

  ![screenshot](../captures/walk2/sec-11-im-vendor-rtv.png)
- `sec-12-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk2/sec-12-im-vendor-purchase-returns.png)
- `flt-07-im-vendor-rtv-a-default.png`

  ![screenshot](../captures/walk3/flt-07-im-vendor-rtv-a-default.png)
- `flt-08-im-vendor-purchase-returns-a-default.png`

  ![screenshot](../captures/walk3/flt-08-im-vendor-purchase-returns-a-default.png)
- `d07-im-vendor-rtv.png`

  ![screenshot](../captures/walk4/d07-im-vendor-rtv.png)
- `d08-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk4/d08-im-vendor-purchase-returns.png)
- `v05-im-vendor-rtv.png`

  ![screenshot](../captures/walk5/v05-im-vendor-rtv.png)
- `v06-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk5/v06-im-vendor-purchase-returns.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]] · [[Vendor-Performance-Scores]]
