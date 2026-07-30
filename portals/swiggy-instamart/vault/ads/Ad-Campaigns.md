---
title: Ad Campaigns
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Ad Campaigns

> Every ad campaign, its budget, pacing and state.

**Campaigns** (`/instamart/campaign/list`, `/instamart/ads`,
`/instamart/advertisement`) is the ads-spend surface. `/api/v1/campaigns` returns
the campaign list with a **33-field** `campaign` object each: id, name, start/end
time, status and status-update reason, bidding strategy, budget (total, pacing
strategy, budget type, rollover flag), campaign criteria, ad groups with their
ads and bids, creation source and full created/updated/status-changed audit
trail with the acting email.

Live for **Jivo Wellness**: `totalCampaigns` = **27**, of which the page rendered
**10** (`paginationContext.size` = 10). Jivo Mart and the `Jivo` brand account
reported **0** campaigns each. Example row: *"Olive Oil (Early & Late)"*,
`CAMPAIGN_AD_TYPE_SPONSORED_PRODUCT`, `CAMPAIGN_STATUS_STOPPED`,
`BUDGET_TYPE_DAILY`, last touched by `ecom1@jivo.in` on 2025-12-31.

**Endpoints in this section:** 14 (3 read, 8 write/export, 3 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/campaign/suggest-budget` | `SUGGEST_BUDGET` | documented (not observed live) | call site .post() on SUGGEST_BUDGET |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/campaigns` | `BRAND_INSIGHTS_CAMPAIGNS` | **PROVEN LIVE 200** | call site .post() on BRAND_INSIGHTS_CAMPAIGNS | live: ['POST'] -> [200], 84274B |
| READ | GET | `partner-api.swiggy.com/instamart/v1/campaign/bpo` | `CAMPAIGN_GET_BPO` | documented (not observed live) | call site .get() on CAMPAIGN_GET_BPO |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/api/v1/bidding-events` | `FESTIVAL_BID_BOOSTER` | WRITE — call site .post() on FESTIVAL_BID_BOOSTER |
| POST | `brand-portal-service-http.swiggy.com/api/v1/campaign` | `CAMPAIGN_CREATE,CAMPAIGN_UPDATE,UPDATE_CAMPAIGN,CAMPAIGN_GET_BPS` | WRITE — call site .post() on CAMPAIGN_CREATE |
| POST | `brand-portal-service-http.swiggy.com/api/v1/campaign/batch` | `UPDATE_BIDS_KEY_UPDATE,UPDATE_KEYWORD_BIDS,BATCH_CAMPAIGN_UPDATE` | WRITE — call site .post() on UPDATE_KEYWORD_BIDS |
| PUT | `brand-portal-service-http.swiggy.com/api/v1/campaign/pause` | `CAMPAIGN_PAUSE` | WRITE — call site .put() on CAMPAIGN_PAUSE |
| POST | `brand-portal-service-http.swiggy.com/api/v1/campaign/resume` | `CAMPAIGN_RESUME` | WRITE — call site .post() on CAMPAIGN_RESUME |
| UNKNOWN | `partner-api.swiggy.com/instamart/v1/campaign/create` | `—` | WRITE — mutating path token(s) ['create'] |
| POST | `partner-api.swiggy.com/instamart/v1/campaign/deactivate` | `CAMPAIGN_DEACTIVATE` | WRITE — call site .post() on CAMPAIGN_DEACTIVATE |
| UNKNOWN | `partner-api.swiggy.com/instamart/v1/campaign/update` | `—` | WRITE — mutating path token(s) ['update'] |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| UNKNOWN | `brand-portal-service-http.swiggy.com/api/v1/campaign/estimate-metric` | `GET_CAMPAIGN_IMPRESSIONS` | read-shaped path but METHOD UNRESOLVED — denied per G1 |
| UNKNOWN | `partner-api.swiggy.com/instamart/v1/campaign` | `CAMPAIGN_GET` | method unresolved from the minified source — denied per G1 |
| UNKNOWN | `partner-api.swiggy.com/instamart/v1/campaign/list` | `CAMPAIGN_LIST` | read-shaped path but METHOD UNRESOLVED — denied per G1 |

## Gotchas

- **27 vs 10 is the pagination trap in one line.** Read `totalCampaigns`, never
  count the rows on screen.
- Campaign create / update / pause / resume / deactivate and every bid or budget
  write are excluded — **ad campaigns spend real money**. `/api/v1/campaign`
  serves create *and* update on the same path, so the whole path is denied even
  though a GET-shaped constant (`CAMPAIGN_GET_BPS`) also points at it.
- `campaignPolicyValidationFailures` is where Swiggy reports why a campaign was
  rejected — worth reading, never writing.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-27-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-27-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png)
- `sec-28-instamart-ads-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-28-instamart-ads-Jivo-Mart-Pvt-Ltd-.png)
- `sec-29-instamart-advertisement-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk2/sec-29-instamart-advertisement-Jivo-Mart-Pvt-Ltd-.png)
- `sec-47-instamart-campaign-list-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-47-instamart-campaign-list-Jivo-Wellness-.png)
- `sec-48-instamart-ads-Jivo-Wellness-.png`

  ![screenshot](../captures/walk2/sec-48-instamart-ads-Jivo-Wellness-.png)
- `sec-67-instamart-campaign-list-Jivo-.png`

  ![screenshot](../captures/walk2/sec-67-instamart-campaign-list-Jivo-.png)
- `sec-68-instamart-ads-Jivo-.png`

  ![screenshot](../captures/walk2/sec-68-instamart-ads-Jivo-.png)
- `d22-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d22-instamart-campaign-list-Jivo-Mart-Pvt-Ltd-.png)
- `d23-instamart-ads-Jivo-Mart-Pvt-Ltd-.png`

  ![screenshot](../captures/walk4/d23-instamart-ads-Jivo-Mart-Pvt-Ltd-.png)
- `d41-instamart-campaign-list-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d41-instamart-campaign-list-Jivo-Wellness-.png)
- `d42-instamart-ads-Jivo-Wellness-.png`

  ![screenshot](../captures/walk4/d42-instamart-ads-Jivo-Wellness-.png)
- `d60-instamart-campaign-list-Jivo-.png`

  ![screenshot](../captures/walk4/d60-instamart-campaign-list-Jivo-.png)
- `d61-instamart-ads-Jivo-.png`

  ![screenshot](../captures/walk4/d61-instamart-ads-Jivo-.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
