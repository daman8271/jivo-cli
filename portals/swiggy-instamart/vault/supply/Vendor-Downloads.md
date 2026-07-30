---
title: Vendor Downloads
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Vendor Downloads

> The vendor lane's report queue and access scope.

**Downloads** (`/im-vendor/downloads`, filed under `Finance` in the nav) is the
vendor lane's report queue: report type, requested date, the filters the report
was generated with, and the download action. `vendorPortal/accessInfo` is the
call every vendor page makes on mount to establish what the signed-in user may
see — it is the vendor lane's authorization probe.

**Endpoints in this section:** 1 (1 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | GET | `picker.swiggy.com/api/v1/vendorPortal/accessInfo` | `—` | **PROVEN LIVE 200** | nearest client .get() after the template url | live: ['GET'] -> [200], 381B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- The queue header reads **"Reports created in the last 7 days"** with an
  explicit date range. That 7-day window is a display default, not the retention
  limit.
- **This section turned out to be the way into the whole inventory dataset.**
  `batch/list` reports **`total_records_count` = 101** completed export jobs that
  `ecom1@jivo.in` has already generated. Downloading an already-completed row is a
  READ (AMENDMENT-02 permits it explicitly); **generating** one is a WRITE (G2) and
  was never done. Three existing exports were downloaded and aggregated — see
  [[Swiggy-Instamart-Data-Inventory]] section 3b for the numbers, including
  **Rs 2.84 Cr of `PotentialGmvLoss`** across 735 SKU x facility rows.
- Job types seen: `VENDOR_PORTAL_GENERATE_ITEM_INVENTORY_DOCUMENTS`,
  `VENDOR_PORTAL_GENERATE_GOODS_RECEIVE_NOTE_DOCUMENTS`,
  `VENDOR_PORTAL_GENERATE_PURCHASE_ORDER_DOCUMENTS`.
- Output files land on a **fifth S3 bucket**,
  `scm-procurement-mumbai.s3.ap-south-1.amazonaws.com/inventory-downloads/csv/`,
  distinct from the ads lane's `im-brand-reports-in-west` bucket.
- The first walk saw the queue as empty; a later pass saw a completed
  **Stock On Hand / 29 Jul 2026** row. So "empty" here means "nothing in the
  display window", not "no reports exist".

## Screenshots (live read-only walk, 2026-07-30)

- `sec-14-im-vendor-downloads.png`

  ![screenshot](../captures/walk1/sec-14-im-vendor-downloads.png)
- `sec-13-im-vendor-downloads.png`

  ![screenshot](../captures/walk2/sec-13-im-vendor-downloads.png)
- `flt-09-im-vendor-downloads-a-default.png`

  ![screenshot](../captures/walk3/flt-09-im-vendor-downloads-a-default.png)
- `d09-im-vendor-downloads.png`

  ![screenshot](../captures/walk4/d09-im-vendor-downloads.png)
- `v09-im-vendor-downloads.png`

  ![screenshot](../captures/walk5/v09-im-vendor-downloads.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
