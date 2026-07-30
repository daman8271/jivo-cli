---
title: Goods Received GRN
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Goods Received GRN

> What Swiggy's facilities actually received against each PO.

**Goods Received** (`/im-vendor/grn`) is the receipt side of the PO lifecycle: the
GRN (Goods Receipt Note) records what a Swiggy facility physically accepted
against a purchase order, at header level (`searchGrns`) and line level
(`grn/searchGrnLines`). Short-receipt and rejection quantities visible here are
what reconcile PO ordered-qty against invoiced qty, so this is the surface that
explains fill-rate gaps.

**Endpoints in this section:** 3 (2 read, 0 write/export, 1 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `picker.swiggy.com/api/v1/grn/searchGrnLines` | `—` | documented (not observed live) | nearest client .post() after the template url |
| READ | POST | `picker.swiggy.com/api/v1/searchGrns` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 77B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| UNKNOWN | `picker.swiggy.com/api/v1/grn-list-data` | `GET_GRN_DATA` | read-shaped path but METHOD UNRESOLVED — denied per G1 |

## Gotchas

- The GRN response carries `total_number_of_grn_records` at header level and
  `total_records_count` at line level — **those are the true totals**, not the
  rows drawn on screen.
- Vendor/warehouse-scoped like the rest of the lane; unfiltered = empty.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-08-im-vendor-grn.png`

  ![screenshot](../captures/walk1/sec-08-im-vendor-grn.png)
- `sec-07-im-vendor-grn.png`

  ![screenshot](../captures/walk2/sec-07-im-vendor-grn.png)
- `flt-03-im-vendor-grn-a-default.png`

  ![screenshot](../captures/walk3/flt-03-im-vendor-grn-a-default.png)
- `d03-im-vendor-grn.png`

  ![screenshot](../captures/walk4/d03-im-vendor-grn.png)
- `v04-im-vendor-grn.png`

  ![screenshot](../captures/walk5/v04-im-vendor-grn.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]] · [[Vendor-Performance-Scores]]
