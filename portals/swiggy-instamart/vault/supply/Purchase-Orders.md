---
title: Purchase Orders
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Purchase Orders

> Every PO Swiggy Instamart raises against JIVO's supplying vendors.

The **Purchase Orders** surface (`/im-vendor/po-dashboard`) is the inbound-demand
view of the Supply Portal: every purchase order Swiggy Instamart has raised
against the distributors that supply JIVO product into its dark stores. A PO row
carries a PO number, a BU type (`MOQ`, `Multi-GRN`), the receiving facility, the
vendor name + vendor code, created/expiry dates, ordered quantity, a rank, and a
booking start date.

This is the lane JIVO's own automation has **never** touched — the daily cron
pulls a sales xlsx from the *ads* portal and nothing from the supply portal at
all. Everything documented here is new surface.

**Endpoints in this section:** 5 (4 read, 0 write/export, 1 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `picker.swiggy.com/api/v1/listAllFCs` | `—` | **PROVEN LIVE 200** | PROVEN LIVE — the app fired POST during a page render and got HTTP [200] with 11949B of JSON | live: ['POST'] -> [200], 11949B |
| READ | POST | `picker.swiggy.com/api/v1/listPurchaseOrderLines` | `GET_ITEM_LIST_DATA` | documented (not observed live) | nearest client .post() after the template url |
| READ | POST | `picker.swiggy.com/api/v1/purchaseMetrics` | `—` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | nearest client .post() after the template url | live: ['POST'] -> [403], 77B |
| READ | POST | `picker.swiggy.com/api/v1/searchPurchaseOrder` | `GET_PO_DETAILS` | **PROVEN LIVE 200,403** | call site .post() on GET_PO_DETAILS | live: ['POST'] -> [200, 403], 31699B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| UNKNOWN | `picker.swiggy.com/api/v1/suppliers/searchSuppliers` | `—` | read-shaped path but METHOD UNRESOLVED — denied per G1 |

## Gotchas

- The dashboard status filter offers **All POs · Open · Partially Open ·
  Completed · Expired · Cancelled**, and defaults to a **`Last 30 Days`** window —
  so the first screen is never the whole PO book.
- The grid is **vendor/warehouse-scoped**: with no vendor or warehouse selected
  several sibling pages render as empty (`No data available for Selected
  Filters`) even though data exists. A count read off an unfiltered screen is
  meaningless.
- `Download Data` on this page is a **report generation** control — a WRITE under
  G2 and never clicked.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-05-im-vendor.png`

  ![screenshot](../captures/walk1/sec-05-im-vendor.png)
- `sec-06-im-vendor-po-dashboard.png`

  ![screenshot](../captures/walk1/sec-06-im-vendor-po-dashboard.png)
- `sec-07-im-vendor-po-booking.png`

  ![screenshot](../captures/walk1/sec-07-im-vendor-po-booking.png)
- `sec-08-im-vendor-grn.png`

  ![screenshot](../captures/walk1/sec-08-im-vendor-grn.png)
- `sec-09-im-vendor-stock-on-hand.png`

  ![screenshot](../captures/walk1/sec-09-im-vendor-stock-on-hand.png)
- `sec-10-im-vendor-low-stock.png`

  ![screenshot](../captures/walk1/sec-10-im-vendor-low-stock.png)
- `sec-11-im-vendor-availability.png`

  ![screenshot](../captures/walk1/sec-11-im-vendor-availability.png)
- `sec-12-im-vendor-rtv.png`

  ![screenshot](../captures/walk1/sec-12-im-vendor-rtv.png)
- `sec-13-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk1/sec-13-im-vendor-purchase-returns.png)
- `sec-14-im-vendor-downloads.png`

  ![screenshot](../captures/walk1/sec-14-im-vendor-downloads.png)
- `sec-15-im-vendor-faq.png`

  ![screenshot](../captures/walk1/sec-15-im-vendor-faq.png)
- `sec-16-im-vendor-performance-vendor-scores.png`

  ![screenshot](../captures/walk1/sec-16-im-vendor-performance-vendor-scores.png)
- `sec-17-im-vendor-performance-item-list-view.png`

  ![screenshot](../captures/walk1/sec-17-im-vendor-performance-item-list-view.png)
- `sec-18-im-vendor-performance-facility-view.png`

  ![screenshot](../captures/walk1/sec-18-im-vendor-performance-facility-view.png)
- `sec-19-im-vendor-local-buying.png`

  ![screenshot](../captures/walk1/sec-19-im-vendor-local-buying.png)
- `sec-20-im-vendor-local-buying-home.png`

  ![screenshot](../captures/walk1/sec-20-im-vendor-local-buying-home.png)
- `sec-21-im-vendor-local-buying-po-summary.png`

  ![screenshot](../captures/walk1/sec-21-im-vendor-local-buying-po-summary.png)
- `sec-22-im-vendor-local-buying-request-summary.png`

  ![screenshot](../captures/walk1/sec-22-im-vendor-local-buying-request-summary.png)
- `sec-05-im-vendor-po-dashboard.png`

  ![screenshot](../captures/walk2/sec-05-im-vendor-po-dashboard.png)
- `sec-06-im-vendor-po-booking.png`

  ![screenshot](../captures/walk2/sec-06-im-vendor-po-booking.png)
- `sec-07-im-vendor-grn.png`

  ![screenshot](../captures/walk2/sec-07-im-vendor-grn.png)
- `sec-08-im-vendor-stock-on-hand.png`

  ![screenshot](../captures/walk2/sec-08-im-vendor-stock-on-hand.png)
- `sec-09-im-vendor-low-stock.png`

  ![screenshot](../captures/walk2/sec-09-im-vendor-low-stock.png)
- `sec-10-im-vendor-availability.png`

  ![screenshot](../captures/walk2/sec-10-im-vendor-availability.png)
- `sec-11-im-vendor-rtv.png`

  ![screenshot](../captures/walk2/sec-11-im-vendor-rtv.png)
- `sec-12-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk2/sec-12-im-vendor-purchase-returns.png)
- `sec-13-im-vendor-downloads.png`

  ![screenshot](../captures/walk2/sec-13-im-vendor-downloads.png)
- `sec-14-im-vendor-faq.png`

  ![screenshot](../captures/walk2/sec-14-im-vendor-faq.png)
- `sec-15-im-vendor-performance-vendor-scores.png`

  ![screenshot](../captures/walk2/sec-15-im-vendor-performance-vendor-scores.png)
- `sec-16-im-vendor-performance-item-list-view.png`

  ![screenshot](../captures/walk2/sec-16-im-vendor-performance-item-list-view.png)
- `sec-17-im-vendor-performance-facility-view.png`

  ![screenshot](../captures/walk2/sec-17-im-vendor-performance-facility-view.png)
- `sec-18-im-vendor-local-buying-home.png`

  ![screenshot](../captures/walk2/sec-18-im-vendor-local-buying-home.png)
- `sec-19-im-vendor-local-buying-po-summary.png`

  ![screenshot](../captures/walk2/sec-19-im-vendor-local-buying-po-summary.png)
- `sec-20-im-vendor-local-buying-request-summary.png`

  ![screenshot](../captures/walk2/sec-20-im-vendor-local-buying-request-summary.png)
- `flt-01-im-vendor-po-dashboard-a-default.png`

  ![screenshot](../captures/walk3/flt-01-im-vendor-po-dashboard-a-default.png)
- `flt-01-im-vendor-po-dashboard-b-widened.png`

  ![screenshot](../captures/walk3/flt-01-im-vendor-po-dashboard-b-widened.png)
- `flt-02-im-vendor-po-booking-a-default.png`

  ![screenshot](../captures/walk3/flt-02-im-vendor-po-booking-a-default.png)
- `flt-03-im-vendor-grn-a-default.png`

  ![screenshot](../captures/walk3/flt-03-im-vendor-grn-a-default.png)
- `flt-04-im-vendor-stock-on-hand-a-default.png`

  ![screenshot](../captures/walk3/flt-04-im-vendor-stock-on-hand-a-default.png)
- `flt-05-im-vendor-low-stock-a-default.png`

  ![screenshot](../captures/walk3/flt-05-im-vendor-low-stock-a-default.png)
- `flt-06-im-vendor-availability-a-default.png`

  ![screenshot](../captures/walk3/flt-06-im-vendor-availability-a-default.png)
- `flt-06-im-vendor-availability-b-widened.png`

  ![screenshot](../captures/walk3/flt-06-im-vendor-availability-b-widened.png)
- `flt-07-im-vendor-rtv-a-default.png`

  ![screenshot](../captures/walk3/flt-07-im-vendor-rtv-a-default.png)
- `flt-08-im-vendor-purchase-returns-a-default.png`

  ![screenshot](../captures/walk3/flt-08-im-vendor-purchase-returns-a-default.png)
- `flt-09-im-vendor-downloads-a-default.png`

  ![screenshot](../captures/walk3/flt-09-im-vendor-downloads-a-default.png)
- `flt-10-im-vendor-performance-vendor-scores-a-default.png`

  ![screenshot](../captures/walk3/flt-10-im-vendor-performance-vendor-scores-a-default.png)
- `flt-11-im-vendor-performance-item-list-view-a-default.png`

  ![screenshot](../captures/walk3/flt-11-im-vendor-performance-item-list-view-a-default.png)
- `flt-12-im-vendor-performance-facility-view-a-default.png`

  ![screenshot](../captures/walk3/flt-12-im-vendor-performance-facility-view-a-default.png)
- `flt-13-im-vendor-faq-a-default.png`

  ![screenshot](../captures/walk3/flt-13-im-vendor-faq-a-default.png)
- `d01-im-vendor-po-dashboard-All-POs.png`

  ![screenshot](../captures/walk4/d01-im-vendor-po-dashboard-All-POs.png)
- `d02-im-vendor-po-booking-Pending-POs.png`

  ![screenshot](../captures/walk4/d02-im-vendor-po-booking-Pending-POs.png)
- `d03-im-vendor-grn.png`

  ![screenshot](../captures/walk4/d03-im-vendor-grn.png)
- `d04-im-vendor-stock-on-hand-Detailed-View.png`

  ![screenshot](../captures/walk4/d04-im-vendor-stock-on-hand-Detailed-View.png)
- `d05-im-vendor-low-stock.png`

  ![screenshot](../captures/walk4/d05-im-vendor-low-stock.png)
- `d06-im-vendor-availability.png`

  ![screenshot](../captures/walk4/d06-im-vendor-availability.png)
- `d07-im-vendor-rtv.png`

  ![screenshot](../captures/walk4/d07-im-vendor-rtv.png)
- `d08-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk4/d08-im-vendor-purchase-returns.png)
- `d09-im-vendor-downloads.png`

  ![screenshot](../captures/walk4/d09-im-vendor-downloads.png)
- `d12-im-vendor-performance-item-list-view.png`

  ![screenshot](../captures/walk4/d12-im-vendor-performance-item-list-view.png)
- `d13-im-vendor-performance-facility-view.png`

  ![screenshot](../captures/walk4/d13-im-vendor-performance-facility-view.png)
- `d14-im-vendor-local-buying-home.png`

  ![screenshot](../captures/walk4/d14-im-vendor-local-buying-home.png)
- `d15-im-vendor-local-buying-po-summary.png`

  ![screenshot](../captures/walk4/d15-im-vendor-local-buying-po-summary.png)
- `d16-im-vendor-local-buying-request-summary.png`

  ![screenshot](../captures/walk4/d16-im-vendor-local-buying-request-summary.png)
- `v01-im-vendor-stock-on-hand.png`

  ![screenshot](../captures/walk5/v01-im-vendor-stock-on-hand.png)
- `v02-im-vendor-low-stock.png`

  ![screenshot](../captures/walk5/v02-im-vendor-low-stock.png)
- `v03-im-vendor-availability.png`

  ![screenshot](../captures/walk5/v03-im-vendor-availability.png)
- `v04-im-vendor-grn.png`

  ![screenshot](../captures/walk5/v04-im-vendor-grn.png)
- `v05-im-vendor-rtv.png`

  ![screenshot](../captures/walk5/v05-im-vendor-rtv.png)
- `v06-im-vendor-purchase-returns.png`

  ![screenshot](../captures/walk5/v06-im-vendor-purchase-returns.png)
- `v07-im-vendor-performance-vendor-scores.png`

  ![screenshot](../captures/walk5/v07-im-vendor-performance-vendor-scores.png)
- `v08-im-vendor-po-dashboard.png`

  ![screenshot](../captures/walk5/v08-im-vendor-po-dashboard.png)
- `v09-im-vendor-downloads.png`

  ![screenshot](../captures/walk5/v09-im-vendor-downloads.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]] · [[Vendor-Performance-Scores]]
