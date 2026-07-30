---
title: Brandverse
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, brand, brand]
status: studied
---


# Brandverse

> Swiggy's cross-platform brand campaign product.

**Brandverse** (`/brandverse/overview`, `/brandverse/campaign-metrics`) is the
`brandverseClient` remote — Swiggy's cross-surface brand-campaign product,
reaching beyond Instamart into the wider Swiggy app. It talks to
`brand-portal-service` under a **third-party** metrics path
(`/api/v1/3p/advertiser/metrics/batch`) and its client identifies itself with
`x-client-id: BRANDVERSE_CLIENT`.

Its dimension vocabulary includes `DIMENSION_TYPE_CAMPAIGN_NAME` and a
`FILTERS_CAMPAIGN_LIST` query, and the UI offers an "All Brandverse Campaigns"
selector.

**Endpoints in this section:** 1 (1 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/3p/advertiser/metrics/batch` | `BATCH_METRICS` | **PROVEN LIVE 403** — endpoint exists and responded; the app called it before a required filter was chosen, so its success shape is NOT captured | call site .post() on BATCH_METRICS | live: ['POST'] -> [403], 69B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- The one Brandverse data call returned **HTTP 403** for `ecom1@jivo.in` — the
  remote loads and renders but the account is **not entitled** to its metrics.
  That is a role-denied finding, recorded as such.
- Whether JIVO has ever run a Brandverse campaign therefore cannot be answered
  from this session; it needs an account with the entitlement.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-37-brandverse-overview-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-37-brandverse-overview-Jivo-Mart-Pvt-Ltd-.png)
- `sec-38-brandverse-campaign-metrics-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-38-brandverse-campaign-metrics-Jivo-Mart-Pvt-Ltd-.png)
- `sec-57-brandverse-overview-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-57-brandverse-overview-Jivo-Wellness-.png)
- `sec-58-brandverse-campaign-metrics-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-58-brandverse-campaign-metrics-Jivo-Wellness-.png)
- `sec-77-brandverse-overview-Jivo-.png`

  ![screenshot](../captures/walk2/sec-77-brandverse-overview-Jivo-.png)
- `sec-78-brandverse-campaign-metrics-Jivo-.png`

  ![screenshot](../captures/walk2/sec-78-brandverse-campaign-metrics-Jivo-.png)
- `d31-brandverse-overview-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d31-brandverse-overview-Jivo-Mart-Pvt-Ltd-.png)
- `d32-brandverse-campaign-metrics-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d32-brandverse-campaign-metrics-Jivo-Mart-Pvt-Ltd-.png)
- `d50-brandverse-overview-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d50-brandverse-overview-Jivo-Wellness-.png)
- `d51-brandverse-campaign-metrics-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d51-brandverse-campaign-metrics-Jivo-Wellness-.png)
- `d69-brandverse-overview-Jivo-.png`

  ![screenshot](../captures/walk4/d69-brandverse-overview-Jivo-.png)
- `d70-brandverse-campaign-metrics-Jivo-.png`

  ![screenshot](../captures/walk4/d70-brandverse-campaign-metrics-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
