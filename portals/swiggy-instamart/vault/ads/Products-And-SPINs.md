---
title: Products And SPINs
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Products And SPINs

> JIVO's product catalogue as the ads platform sees it.

Product lookup for campaign targeting and reporting: `products/filter` (by
brand), `products/search` (free text), `products/batch` (bulk fetch by id) and
the sampling remote's `spins` / `spins/batch`. Swiggy's product identifier is the
**SPIN** (e.g. `L7P0RZ1JUI`), which is the join key between the ads surface, the
catalog surface and the sales report xlsx.

Live, the sales filter reported **37 products with sales in window** for Jivo
Wellness against **12** for Jivo Mart.

**Endpoints in this section:** 4 (4 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/products/batch` | `GET_PRODUCTS_BATCH` | documented (not observed live) | call site .post() on GET_PRODUCTS_BATCH |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/products/filter` | `LIST_PRODUCTS_BY_BRAND` | documented (not observed live) | call site .post() on LIST_PRODUCTS_BY_BRAND |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/products/search` | `SEARCH_PRODUCTS` | documented (not observed live) | call site .post() on SEARCH_PRODUCTS |
| READ | POST | `partner-api.swiggy.com/instamart/v1/products/filter` | `PRODUCTS_FILTER` | documented (not observed live) | call site .post() on PRODUCTS_FILTER |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- SPIN is the identifier to key on across every Swiggy surface — not EAN, not
  JIVO's item code. The sales xlsx `ITEM_CODE` column maps to it.
- "Products with sales in window" (37) is smaller than "SPINs listed" (43): the
  gap is listed-but-not-selling, which is exactly the number worth watching.

## Screenshots (live read-only walk, 2026-07-30)

_No screenshot is attributed to this section; its endpoints are exercised from pages captured under sibling notes. See [[Swiggy-Instamart-Screenshot-Index]] for the full set._

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
