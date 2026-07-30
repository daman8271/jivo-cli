---
title: NPI New Product Introduction
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# NPI New Product Introduction

> New Product Introduction pipeline.

**NPI** (`/instamart/npi`) is the New Product Introduction surface — the pipeline
by which a new SKU gets listed onto Instamart. The config flag `NPI_ENABLED` is
**true** for this account and the walk saw NPI-tagged catalog images
(`NPI-152297`, `NPI-151560`, `NPI-151565`, `NPI-151592`, `NPI-151593`,
`NPI-151561`, `NPI-151573`, all dated 2026-07-16) being loaded by the catalog
surface, which means there is live NPI activity on JIVO's account.

The route renders inside the ads remote and shares the placement-suggestion
endpoint.

**Endpoints in this section:** 1 (1 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/suggest-placement` | `SUGGEST_PLACEMENT` | documented (not observed live) | call site .post() on SUGGEST_PLACEMENT |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- The NPI ids seen came from **image URLs** the page loaded, not from a JSON
  response — good enough to prove activity and a date, not enough to enumerate
  the pipeline. Recorded as evidence of activity, not as a count.
- NPI submission is a write surface; only the listing view was opened.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-31-instamart-npi-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-31-instamart-npi-Jivo-Mart-Pvt-Ltd-.png)
- `d25-instamart-npi-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d25-instamart-npi-Jivo-Mart-Pvt-Ltd-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
