---
title: Stock On Hand and Low Stock
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Stock On Hand and Low Stock

> Dark-store level inventory, days-on-hand and low-stock alerts.

**Stock On Hand** (`/im-vendor/stock-on-hand`) and **Low Inventory**
(`/im-vendor/low-stock`) are the inventory surfaces of the Supply Portal. Stock
On Hand offers a `Real Time Summary` and a `Detailed View` with per-facility,
per-product quantity available, **DOH** (days-on-hand), open POs and open PO
quantity. The summary tiles are High Risk Items (DOH <= 1), Low Stock Items
(1 < DOH <= 5), Total Inventory Count and Total Inventory Value.

`inventory/search/lowStockFcs` is the facility-level low-stock list; this is the
closest thing Swiggy exposes to a stock-out early-warning feed, and JIVO reads
none of it today.

**Endpoints in this section:** 3 (3 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `picker.swiggy.com/api/v1/inventory/metrics` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 50B |
| READ | POST | `picker.swiggy.com/api/v1/inventory/search/itemInventories` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 50B |
| READ | POST | `picker.swiggy.com/api/v1/inventory/search/lowStockFcs` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 50B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- **The empty-state trap:** with no vendor/warehouse selected the tiles read
  `High Risk Items 0 · Low Stock Items 0 · Total Inventory Count 0 · Total
  Inventory Value Rs 0` and the grid says `No data available for Selected
  Filters`. Those zeros are **not** JIVO's inventory — they are an unfiltered
  query. Any number taken from this page must name its vendor + warehouse filter.
- `Bulk Download` is a report-generation control → WRITE under G2, never clicked.
- **The grid could not be driven, and the numbers were obtained anyway.** A fifth
  pass seeded `__IM_VENDOR_BRAND_ID__` (client-side, in a copy of the profile) and
  the grid still rendered empty; a DOM dump proved these pages expose **no standard
  `<select>` or combobox at all** (0 selects, 0 comboboxes, 0-1 checkboxes), which is
  also why the earlier filter-widening clicks produced byte-identical before/after
  screenshots. The real inventory data came instead from an **already-generated
  export** in [[Vendor-Downloads]] — 735 SKU x facility rows with `DaysOnHand`,
  `PotentialGmvLoss`, `OpenPos`, `OpenPoQuantity` and `WarehouseQtyAvailable`.
  See [[Swiggy-Instamart-Data-Inventory]] section 3b.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-09-im-vendor-stock-on-hand.png`

  ![screenshot](../captures/walk1/sec-09-im-vendor-stock-on-hand.png)
- `sec-10-im-vendor-low-stock.png`

  ![screenshot](../captures/walk1/sec-10-im-vendor-low-stock.png)
- `sec-08-im-vendor-stock-on-hand.png`

  ![screenshot](../captures/walk2/sec-08-im-vendor-stock-on-hand.png)
- `sec-09-im-vendor-low-stock.png`

  ![screenshot](../captures/walk2/sec-09-im-vendor-low-stock.png)
- `flt-04-im-vendor-stock-on-hand-a-default.png`

  ![screenshot](../captures/walk3/flt-04-im-vendor-stock-on-hand-a-default.png)
- `flt-05-im-vendor-low-stock-a-default.png`

  ![screenshot](../captures/walk3/flt-05-im-vendor-low-stock-a-default.png)
- `d04-im-vendor-stock-on-hand-Detailed-View.png`

  ![screenshot](../captures/walk4/d04-im-vendor-stock-on-hand-Detailed-View.png)
- `d05-im-vendor-low-stock.png`

  ![screenshot](../captures/walk4/d05-im-vendor-low-stock.png)
- `v01-im-vendor-stock-on-hand.png`

  ![screenshot](../captures/walk5/v01-im-vendor-stock-on-hand.png)
- `v02-im-vendor-low-stock.png`

  ![screenshot](../captures/walk5/v02-im-vendor-low-stock.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Availability-and-Fill-Rate]] · [[Vendor-Performance-Scores]]
