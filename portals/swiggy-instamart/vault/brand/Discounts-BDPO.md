---
title: Discounts BDPO
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, brand, brand]
status: studied
---


# Discounts BDPO

> Brand-funded discount campaigns (BDPO) and their reports.

**Discounts** (`/im-discounts`) is the `imBdpoClient` remote — BDPO is
Swiggy's brand-funded discount mechanism, where JIVO funds a price cut in
exchange for visibility. The remote has its own API family under
`/api/discounting/v1/*` (campaign, campaign search, campaign config, campaigns,
metrics batch, T&C acceptance, upload status) plus an account/config family
mirroring the shell's under `/im-discounts/v1/*`.

Its reports come out through the shared report queue as
`discount/reports` (list) and `discounts/report` / `report/initiate-bdpo-report`
(generate), and the sales-report API has a matching `list-bdpo` variant.

**Endpoints in this section:** 15 (9 read, 3 write/export, 3 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | GET | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/file` | `—` | documented (not observed live) | direct literal call site .get("api/discounting/v1/campaign/file") |
| READ | POST | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/search` | `—` | documented (not observed live) | direct literal call site .post("/api/discounting/v1/campaign/search") |
| READ | GET | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/spins` | `—` | documented (not observed live) | direct literal call site .get("api/discounting/v1/campaign/spins") |
| READ | POST | `brand-portal-service-http.swiggy.com/api/discounting/v1/metrics/batch` | `—` | documented (not observed live) | direct literal call site .post("/api/discounting/v1/metrics/batch") |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/discount/reports` | `LIST_DISCOUNTS_REPORTS` | **PROVEN LIVE 200** | call site .post() on LIST_DISCOUNTS_REPORTS | live: ['POST'] -> [200], 35B |
| READ | GET | `partner-api.swiggy.com/im-discounts/v1/account/get` | `—` | documented (not observed live) | direct literal call site .get("/im-discounts/v1/account/get") |
| READ | GET | `partner-api.swiggy.com/im-discounts/v1/account/list` | `—` | documented (not observed live) | direct literal call site .get("/im-discounts/v1/account/list") |
| READ | GET | `partner-api.swiggy.com/im-discounts/v1/account/permissions` | `—` | documented (not observed live) | direct literal call site .get("/im-discounts/v1/account/permissions") |
| READ | GET | `partner-api.swiggy.com/im-discounts/v1/configs` | `—` | documented (not observed live) | direct literal call site .get("/im-discounts/v1/configs") |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| PUT | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/disable` | `—` | WRITE — direct literal call site .put("api/discounting/v1/campaign/disable") |
| GET | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/upload-status` | `—` | WRITE — direct literal call site .get("/api/discounting/v1/campaign/upload-status") |
| POST | `brand-portal-service-http.swiggy.com/api/v1/discounts/report` | `INITIATE_DISCOUNTS_METRIC_REPORT` | EXPORT — call site .post() on INITIATE_DISCOUNTS_METRIC_REPORT |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign` | `—` | direct literal call site .post("/api/discounting/v1/campaign") |
| POST | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaigns` | `—` | direct literal call site .post("/api/discounting/v1/campaigns") |
| POST | `brand-portal-service-http.swiggy.com/api/discounting/v1/tnc/acceptance` | `—` | direct literal call site .post("/api/discounting/v1/tnc/acceptance") — path also served by another verb; kept the mutating one so deny-by-default wins |

## Gotchas

- **Every `/api/discounting/v1/*` endpoint is method-UNRESOLVED** from the
  minified source and therefore denied per G1. They are documented in full here
  and in [[Swiggy-Instamart-Endpoints]] but none is wired into the CLI.
- The host for `/api/discounting/v1/*` (brand-portal-service) and
  `/im-discounts/v1/*` (partner-api) is **INFERRED** from the path-prefix pattern
  the other remotes follow, not observed on the wire — the live walk never got a
  discounts data call to fire.
- `ENABLE_BDPO_MONITORING` and `BDPO_INTEGRATION_FULL_ROLLOUT` are both **true**,
  so this surface is live for JIVO.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-32-im-discounts-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-32-im-discounts-Jivo-Mart-Pvt-Ltd-.png)
- `sec-52-im-discounts-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-52-im-discounts-Jivo-Wellness-.png)
- `sec-72-im-discounts-Jivo-.png`

  ![screenshot](../captures/walk2/sec-72-im-discounts-Jivo-.png)
- `d26-im-discounts-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d26-im-discounts-Jivo-Mart-Pvt-Ltd-.png)
- `d45-im-discounts-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d45-im-discounts-Jivo-Wellness-.png)
- `d64-im-discounts-Jivo-.png`

  ![screenshot](../captures/walk4/d64-im-discounts-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
