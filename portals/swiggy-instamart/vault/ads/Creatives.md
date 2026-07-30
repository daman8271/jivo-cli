---
title: Creatives
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Creatives

> Ad creative library and its (excluded) upload path.

The creative surface covers the pre-approved creative library
(`creative/list`) and creative detail (`creative/details`), which together are
what a campaign's ad units draw from. Alongside them sits
`instamart/v1/creative/get-upload-info-v2`, which issues S3 upload credentials.

**Endpoints in this section:** 3 (2 read, 1 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/creative/details` | `CREATIVE_DETAILS` | documented (not observed live) | call site .post() on CREATIVE_DETAILS |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/creative/list` | `PREAPPROVED_CREATIVES` | documented (not observed live) | call site .post() on PREAPPROVED_CREATIVES |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| GET | `partner-api.swiggy.com/instamart/v1/creative/get-upload-info-v2` | `GET_S3_UPLOAD_INFO` | WRITE — call site .get() on GET_S3_UPLOAD_INFO |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- `get-upload-info-v2` is an **HTTP GET** and its constant is
  `GET_S3_UPLOAD_INFO`, so a naive verb-based rule would admit it. It is
  nevertheless **excluded**: its only purpose is to hand back credentials that
  enable a creative upload. Read-only means not standing next to the write
  either.
- `creative/list`'s constant is `PREAPPROVED_CREATIVES` — an early pass of my
  classifier flagged it WRITE because the string contains "approve". Tokenising
  the constant name (`pre` / `approved` / `creatives`) fixed it; it is a READ.

## Screenshots (live read-only walk, 2026-07-30)

_No screenshot is attributed to this section; its endpoints are exercised from pages captured under sibling notes. See [[Swiggy-Instamart-Screenshot-Index]] for the full set._

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
