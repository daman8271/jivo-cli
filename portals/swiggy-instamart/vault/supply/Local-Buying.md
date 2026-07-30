---
title: Local Buying
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, supply, supply]
status: studied
---


# Local Buying

> The local-buying indent flow — a separate login.

**Local Buying** (`/im-vendor/local-buying/*`) is a distinct sub-application
inside the vendor remote (its own federation entry,
`__federation_expose_LocalBuyingApp`) covering city-level local purchase
indents: an indent list, indent detail, indent line items, and a PO download.

It is the only surface in the study that sits behind a **second, different
login**: the remote resolves a `LOCAL_VENDOR` user pool to an
`influencer-app-*.swig.gy` identity host rather than the ozone brand IdP, and
`/im-vendor/local-buying/login` is its own login route.

**Endpoints in this section:** 7 (4 read, 3 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `picker.swiggy.com/api/v1/external/indent/get` | `GET_INDENT` | documented (not observed live) | call site .post() on GET_INDENT |
| READ | POST | `picker.swiggy.com/api/v1/external/indent/list_indent_items` | `GET_INDENT_ITEM_LIST` | documented (not observed live) | call site .post() on GET_INDENT_ITEM_LIST |
| READ | POST | `picker.swiggy.com/api/v1/external/indent/list_indents` | `GET_INDENT_LIST` | documented (not observed live) | call site .post() on GET_INDENT_LIST |
| READ_FILE | POST | `picker.swiggy.com/api/v1/external/indent/po/download` | `PO_DOWNLOAD` | documented (not observed live) | call site .post() on PO_DOWNLOAD |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `picker.swiggy.com/api/v1/external/indent/accept` | `ACCEPT_INDENT` | WRITE — call site .post() on ACCEPT_INDENT |
| POST | `picker.swiggy.com/api/v1/external/indent/item/update` | `UPDATE_INDENT,UPDATE_INDENT_ITEM` | WRITE — call site .post() on UPDATE_INDENT_ITEM |
| POST | `picker.swiggy.com/api/v1/external/indent/reject` | `REJECT_INDENT` | WRITE — call site .post() on REJECT_INDENT |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- Walked and screenshotted, but **no data**: every local-buying route rendered
  a shell with **0 API calls** under the `ecom1@jivo.in` session. Marked
  NOT_REACHABLE — needs the separate local-vendor credential, which JIVO may not
  hold at all.
- `indent/accept`, `indent/reject` and `indent/item/update` are writes that
  would accept or reject a real purchase indent. Excluded, never clicked.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-19-im-vendor-local-buying.png`

  ![screenshot](../captures/walk1/sec-19-im-vendor-local-buying.png)
- `sec-20-im-vendor-local-buying-home.png`

  ![screenshot](../captures/walk1/sec-20-im-vendor-local-buying-home.png)
- `sec-21-im-vendor-local-buying-po-summary.png`

  ![screenshot](../captures/walk1/sec-21-im-vendor-local-buying-po-summary.png)
- `sec-22-im-vendor-local-buying-request-summary.png`

  ![screenshot](../captures/walk1/sec-22-im-vendor-local-buying-request-summary.png)
- `sec-18-im-vendor-local-buying-home.png`

  ![screenshot](../captures/walk2/sec-18-im-vendor-local-buying-home.png)
- `sec-19-im-vendor-local-buying-po-summary.png`

  ![screenshot](../captures/walk2/sec-19-im-vendor-local-buying-po-summary.png)
- `sec-20-im-vendor-local-buying-request-summary.png`

  ![screenshot](../captures/walk2/sec-20-im-vendor-local-buying-request-summary.png)
- `d14-im-vendor-local-buying-home.png`

  ![screenshot](../captures/walk4/d14-im-vendor-local-buying-home.png)
- `d15-im-vendor-local-buying-po-summary.png`

  ![screenshot](../captures/walk4/d15-im-vendor-local-buying-po-summary.png)
- `d16-im-vendor-local-buying-request-summary.png`

  ![screenshot](../captures/walk4/d16-im-vendor-local-buying-request-summary.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
