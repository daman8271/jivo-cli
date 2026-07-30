---
title: Availability and Fill Rate
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Availability and Fill Rate

> City/store availability and the fill-rate view.

**Availability** (`/im-vendor/availability`) reports how often JIVO's SKUs were
actually available to buy, sliced by city, facility and category — the
q-commerce metric that decides whether a listed SKU earns anything. It is fed by
`searchInventoryAvailabilityMetrics`, with `category/list` and `brands/list`
supplying its filter vocabularies.

`category/list` returned **94 categories** live; that list is the complete
category filter vocabulary for the vendor lane.

**Endpoints in this section:** 3 (3 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | GET | `picker.swiggy.com/api/v1/brands/list` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .get() after the template url | live: ['GET'] -> [403], 97B |
| READ | GET | `picker.swiggy.com/api/v1/category/list` | `—` | **PROVEN LIVE 200** | nearest client .get() after the template url | live: ['GET'] -> [200], 6666B |
| READ | POST | `picker.swiggy.com/api/v1/searchInventoryAvailabilityMetrics` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 77B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- `searchInventoryAvailabilityMetrics` returned **HTTP 403
  `{"status_code":1,"message":"Invalid Request Body"}`** on the passive render —
  the page issues it before a required filter is chosen. So the endpoint is
  PROVEN to exist and PROVEN to reject an unfiltered call; its success shape is
  **not** captured. Recorded as such rather than guessed.
- Availability is inherently **city- and dark-store-scoped**. A national roll-up
  hides exactly the gaps this page exists to show.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-11-im-vendor-availability.png`

  ![screenshot](../captures/walk1/sec-11-im-vendor-availability.png)
- `sec-10-im-vendor-availability.png`

  ![screenshot](../captures/walk2/sec-10-im-vendor-availability.png)
- `flt-06-im-vendor-availability-a-default.png`

  ![screenshot](../captures/walk3/flt-06-im-vendor-availability-a-default.png)
- `flt-06-im-vendor-availability-b-widened.png`

  ![screenshot](../captures/walk3/flt-06-im-vendor-availability-b-widened.png)
- `d06-im-vendor-availability.png`

  ![screenshot](../captures/walk4/d06-im-vendor-availability.png)
- `v03-im-vendor-availability.png`

  ![screenshot](../captures/walk5/v03-im-vendor-availability.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Vendor-Performance-Scores]]
