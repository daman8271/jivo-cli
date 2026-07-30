---
title: Config And Feature Flags
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, platform, platform]
status: studied
---


# Config And Feature Flags

> 141 cities, 74 config keys, and the portal's whole feature surface.

`GET partner-api.swiggy.com/instamart/v1/configs` is the single most
information-dense endpoint in the portal: **24,655 bytes / 74 keys**, fetched on
every page load. It is the portal telling you exactly what it can do.

- **`IM_ENABLED_CITIES` = 141 cities**, each with an id — the master city
  vocabulary for every city-scoped query in the study.
- **`VENDOR_WHITELISTED_ACCOUNTS` = 198** account ids;
  `BANNER_ADS_WHITELISTED_ACCOUNTS` and
  `SPECIALITY_ADS_WHITELISTED_ACCOUNTS` = **83** each.
- ~60 `*_FULL_ROLLOUT` feature flags naming every ad format and surface Swiggy
  ships: sponsored product, banner, speciality, top-slot (v1 and a gated v2),
  collection ads, pre-search ads, auto-suggest ads, FBT / SwigSmart, one-click
  campaigns, dynamic pricing, festival bid booster, user targeting, keyword SOV,
  budget rollover, ad-slot rank, granular reports, search-query report.
- `CONFIG_TEXTS` carries live commercial parameters, e.g.
  `BID_DISCOUNT_FOR_TOP_SLOT#0.25`.

**Endpoints in this section:** 2 (2 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | GET | `brand-portal-service-http.swiggy.com/api/discounting/v1/campaign/config` | `—` | documented (not observed live) | direct literal call site .get("/api/discounting/v1/campaign/config") |
| READ | GET | `partner-api.swiggy.com/instamart/v1/configs` | `FETCH_CONFIGS` | **PROVEN LIVE 200** | call site .get() on FETCH_CONFIGS | live: ['GET'] -> [200], 24655B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- **Flags that are OFF are as informative as those that are ON.**
  `AI_ASSISTANT_FULL_ROLLOUT`, `REPORTS_V2_FULL_ROLLOUT`,
  `RO_UPLOAD_FULL_ROLLOUT`, `TOP_SLOTV2_FULL_ROLLOUT`,
  `REPORTS_NEW_UI_35_DAYS_WINDOW_ENFORCEMENT_FULL_ROLLOUT` and
  `FEATURE_RESTRICTIONS_FULL_ROLLOUT` are all **false** for this account.
- The 141-city config list is larger than the 132 cities the sales filter
  returns — the gap is cities with no JIVO sales history, and it is a real
  distribution-whitespace signal.
- `FEATURE_CONFIG` came back as an **empty object**; recorded as empty, not
  omitted.

## Screenshots (live read-only walk, 2026-07-30)

_No screenshot is attributed to this section; its endpoints are exercised from pages captured under sibling notes. See [[Swiggy-Instamart-Screenshot-Index]] for the full set._

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
