---
title: Sampling Campaigns
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, brand, brand]
status: studied
---


# Sampling Campaigns

> Product-sampling campaigns to acquire new users.

**Sampling** (`/im-sampling`) is the `imSamplingClient` remote: campaigns that
put JIVO product samples into other customers' orders to acquire new users. The
portal's own promotional copy for it was captured in the config
(`BANNER_POPUP.bannerContainerTitle` = *"Introducing Sampling"*, description
*"Acquire new users by deliv..."*), which is how a surface nobody opened
advertises itself.

`SAMPLING_INTEGRATION_FULL_ROLLOUT` is **true**. The remote exposes campaign
detail and product-SPIN batch lookups, and a reports route.

**Endpoints in this section:** 3 (2 read, 0 write/export, 1 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/campaign/{0}` | `GET_CAMPAIGN_DETAILS` | documented (not observed live) | call site .post() on GET_CAMPAIGN_DETAILS |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/spins/batch` | `GET_PRODUCT_SPINS_BATCH` | documented (not observed live) | call site .post() on GET_PRODUCT_SPINS_BATCH |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/spins` | `GET_SPINS` | read-shaped path but METHOD UNRESOLVED — denied per G1 |

## Gotchas

- Campaign **create** routes exist (`/im-sampling/campaign/create`) and were
  deliberately **not navigated** — a create screen can fire a draft-create call
  on mount, which would be a write. Marked NOT_WALKED with that reason.
- No sampling campaign data was returned for this account, so "is JIVO running
  sampling?" is **not answered** by this study. The surface is mapped; the
  occupancy is unknown.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-35-im-sampling-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-35-im-sampling-Jivo-Mart-Pvt-Ltd-.png)
- `sec-36-im-sampling-reports-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-36-im-sampling-reports-Jivo-Mart-Pvt-Ltd-.png)
- `sec-55-im-sampling-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-55-im-sampling-Jivo-Wellness-.png)
- `sec-56-im-sampling-reports-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-56-im-sampling-reports-Jivo-Wellness-.png)
- `sec-75-im-sampling-Jivo-.png`

  ![screenshot](../captures/walk2/sec-75-im-sampling-Jivo-.png)
- `sec-76-im-sampling-reports-Jivo-.png`

  ![screenshot](../captures/walk2/sec-76-im-sampling-reports-Jivo-.png)
- `d29-im-sampling-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d29-im-sampling-Jivo-Mart-Pvt-Ltd-.png)
- `d30-im-sampling-reports-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d30-im-sampling-reports-Jivo-Mart-Pvt-Ltd-.png)
- `d48-im-sampling-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d48-im-sampling-Jivo-Wellness-.png)
- `d49-im-sampling-reports-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d49-im-sampling-reports-Jivo-Wellness-.png)
- `d67-im-sampling-Jivo-.png`

  ![screenshot](../captures/walk4/d67-im-sampling-Jivo-.png)
- `d68-im-sampling-reports-Jivo-.png`

  ![screenshot](../captures/walk4/d68-im-sampling-reports-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
