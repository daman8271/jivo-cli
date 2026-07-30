---
title: Requisition Orders
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Requisition Orders

> Release / requisition orders — the ads booking documents.

**Requisition Orders** (`/instamart/requisition-orders`) covers release orders
(ROs): the commercial documents behind booked ad inventory. `release-orders/search`
lists them, `release-order` fetches one, and the surface also carries approve and
delete operations.

The `RO_UPLOAD_FULL_ROLLOUT` flag is **false** on this account, so the RO bulk
upload path is not currently active for JIVO.

**Endpoints in this section:** 3 (0 read, 3 write/export, 0 unknown/denied).

## API endpoints

### Read surface

_No read endpoint is assigned to this section — it is a route/UI surface that renders from endpoints documented in sibling notes._

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/release-order` | `RELEASE_ORDER_GET,RELEASE_ORDER_DELETE` | WRITE — mutating path token(s) ['release'] |
| POST | `brand-portal-service-http.swiggy.com/api/v1/release-order/approve` | `RELEASE_ORDER_APPROVE` | WRITE — call site .post() on RELEASE_ORDER_APPROVE |
| POST | `brand-portal-service-http.swiggy.com/api/v1/release-orders/search` | `RELEASE_ORDER_SEARCH` | WRITE — call site .post() on RELEASE_ORDER_SEARCH |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- `/api/v1/release-order` is bound to **two** constants — `RELEASE_ORDER_GET`
  *and* `RELEASE_ORDER_DELETE` — on the same path, distinguished only by HTTP
  method. Deny-by-default applies to the path, so it is excluded even though a
  read exists there. `release-orders/search` (plural, `/search`) is the safe read.
- `release-order/approve` is a commercial approval. Never called.

## Screenshots (live read-only walk, 2026-07-30)

_No screenshot is attributed to this section; its endpoints are exercised from pages captured under sibling notes. See [[Swiggy-Instamart-Screenshot-Index]] for the full set._

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
