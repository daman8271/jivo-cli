---
title: Keyword And Bid Suggestions
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Keyword And Bid Suggestions

> Keyword suggestions, bid guidance, budget and placement recommendations.

A cluster of recommendation endpoints supports campaign construction:
keyword suggestions (`suggest/keyword/bids`, `instamart/v1/keywords/suggestions`),
L2 category placement suggestions, catalog-targeting category paths, suggested
bids inside campaigns, budget suggestions and placement suggestions, plus
`keyword/campaign-insights` for how keywords are actually performing.

These are pure reads that reveal **what Swiggy thinks JIVO should be bidding on**
— the platform's own view of the search demand around edible oil — and none of it
is currently pulled.

**Endpoints in this section:** 6 (3 read, 1 write/export, 2 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/keyword/campaign-insights` | `LIST_KEYWORD_CAMPAIGN_INSIGHTS` | documented (not observed live) | call site .post() on LIST_KEYWORD_CAMPAIGN_INSIGHTS |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/suggest/category-paths` | `SUGGEST_CATALOG_TARGETING` | documented (not observed live) | call site .post() on SUGGEST_CATALOG_TARGETING |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/suggest/keyword/bids` | `KEYWORD_SUGGESTIONS` | documented (not observed live) | call site .post() on KEYWORD_SUGGESTIONS |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/api/v1/campaigns/suggest_bids` | `SUGGEST_BID_IN_CAMPAIGNS,GET_SUGGEST_BIDS` | WRITE — call site .post() on SUGGEST_BID_IN_CAMPAIGNS |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| UNKNOWN | `partner-api.swiggy.com/instamart/v1/keywords/l2-placement-suggestions` | `L2_CATEGORY_SUGGESTIONS` | read-shaped path but METHOD UNRESOLVED — denied per G1 |
| UNKNOWN | `partner-api.swiggy.com/instamart/v1/keywords/suggestions` | `—` | read-shaped path but METHOD UNRESOLVED — denied per G1 |

## Gotchas

- The keyword-insight surface pairs with the `KEYWORD_SOV_FULL_ROLLOUT` and
  `SEARCH_QUERY_REPORT_FULL_ROLLOUT` flags, both **on** for this account: there
  is a search-query report available that JIVO has never generated.
- These endpoints are read-safe but sit inside campaign-editing screens; the
  surrounding Save/Launch controls are forbidden.

## Screenshots (live read-only walk, 2026-07-30)

_No screenshot is attributed to this section; its endpoints are exercised from pages captured under sibling notes. See [[Swiggy-Instamart-Screenshot-Index]] for the full set._

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
