---
title: PO Booking Appointments
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# PO Booking Appointments

> Slot booking for POs into Swiggy fulfilment centres.

**PO Booking** (`/im-vendor/po-booking`) is where a pending PO is turned into a
delivery appointment at a Swiggy facility. It is the richest page in the vendor
lane — the live walk rendered **9,486 characters** of PO rows and captured
**~83 KB** of API responses from a single visit.

The page splits into two views, `Pending POs` and `Scheduled Appointments`, and
exposes a slot recommender (`fc-appointment/recommend-slots`) plus the facility
list (`listAllFCs`) and supplier search that drive its filters.

**Endpoints in this section:** 9 (1 read, 6 write/export, 2 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | GET | `picker.swiggy.com/api/v1/batch/list` | `BATCH_LIST` | **PROVEN LIVE 200** | call site .get() on BATCH_LIST | live: ['POST'] -> [200], 10230B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `picker.swiggy.com/api/v1/batch/submit` | `BULK_DOWNLOAD_PO_DATA` | WRITE — call site .post() on BULK_DOWNLOAD_PO_DATA |
| POST | `picker.swiggy.com/api/v1/document/batch/generate` | `DOWNLOAD_SINGLE_PO_DATA` | EXPORT — call site .post() on DOWNLOAD_SINGLE_PO_DATA |
| POST | `picker.swiggy.com/api/v1/document/merged/generate` | `DOWNLOAD_MULTIPLE_PO_DATA` | EXPORT — call site .post() on DOWNLOAD_MULTIPLE_PO_DATA |
| UNKNOWN | `picker.swiggy.com/api/v1/fc-appointment/batch-cancel` | `—` | WRITE — mutating path token(s) ['cancel'] |
| UNKNOWN | `picker.swiggy.com/api/v1/fc-appointment/batch-create` | `—` | WRITE — mutating path token(s) ['create'] |
| UNKNOWN | `picker.swiggy.com/api/v1/fc-appointment/batch-reschedule` | `—` | WRITE — mutating path token(s) ['reschedule'] |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| UNKNOWN | `picker.swiggy.com/api/v1/fc-appointment/recommend-slots` | `—` | read-shaped path but METHOD UNRESOLVED — denied per G1 |
| UNKNOWN | `picker.swiggy.com/api/v1/fc-appointment/search` | `—` | read-shaped path but METHOD UNRESOLVED — denied per G1 |

## Gotchas

- **This page is the most dangerous surface in the whole study.** `Pick slot/s`,
  `Club selected POs & Book`, and the `batch-create` / `batch-reschedule` /
  `batch-cancel` appointment endpoints all mutate a real delivery booking.
  None of them was clicked and none is in the read allowlist.
- `/api/v1/batch/submit` reads like a read (its constant is
  `BULK_DOWNLOAD_PO_DATA`) but `submit` enqueues a job — treated as a WRITE.
- `document/batch/generate` and `document/merged/generate` are report generation
  → EXPORT, excluded per G2.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-07-im-vendor-po-booking.png`

  ![screenshot](../captures/walk1/sec-07-im-vendor-po-booking.png)
- `sec-06-im-vendor-po-booking.png`

  ![screenshot](../captures/walk2/sec-06-im-vendor-po-booking.png)
- `flt-02-im-vendor-po-booking-a-default.png`

  ![screenshot](../captures/walk3/flt-02-im-vendor-po-booking-a-default.png)
- `d02-im-vendor-po-booking-Pending-POs.png`

  ![screenshot](../captures/walk4/d02-im-vendor-po-booking-Pending-POs.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]] · [[Vendor-Performance-Scores]]
