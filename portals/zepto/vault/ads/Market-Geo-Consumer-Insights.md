---
title: Market, Geo & Consumer Insights
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, ads, market-geo-consumer]
status: studied
---

# Market, Geo & Consumer Insights

The **Market, Geo & Consumer Insights** section is the Zepto brand-analytics
portal's **market-intelligence surface** — the read-only dashboards a JIVO operator
uses to answer "where do I sell, how big is my share, how does price move volume, and
who is my shopper?". It bundles four analytics dashboards: **Geo Insights**
(hyperlocal city / store / product performance on a map), **Market Share** (GMV &
units share, share-of-voice, top-of-search, new-user penetration versus the
category), **Elasticity** (price↔volume, discount-ROI, pack-size, shopper-clock,
trial-to-loyalty curves), and **Persona** (consumer segments, heat-maps, city split).
Every call here is a **pure read** — analytics data fetched by date range and entity;
nothing on this surface mutates Zepto state. For JIVO this is Jivo Wellness Pvt. Ltd.
(`manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / STANDARD
tier), ads brand `b3550d5d-fc71-47b0-af4f-f221f909b936`; requests carry
`manufacturerId` + `startDate`/`endDate` query params (confirmed in the chunk).

The endpoint contracts below were extracted from the **ads** (632) and **vendor**
(635) micro-frontend chunks — the ads geo-dashboard `GS`-enum map (const values like
`GI_GET_SLIDER_DATA`, `GI_GET_HYPERLOCAL_CITY_PERFORMANCE`,
`ads-bff/api/v1/coordinates/decode`) in the ads remote, and the brand-analytics
URL-constant block in `captures/js/vendor/3539.64ab07c46b8741b5.js` (the minified
`brand-analytics-web/api/v1/{geo-analytics,market-share,elasticity,persona}/*`
strings, consumed by that chunk's shared HTTP helper) — **not** live captures except
where a probe is noted. A single host serves the whole surface,
**`fcc.zepto.co.in`**, using the single JWT (`authorization: <jwt>`, **no** `Bearer`
prefix) the whole stack shares; WAF headers were not enforced at last capture.

**Two implementations of the same geo surface.** The ten `api/v1/geo-analytics/*`
reads are the **ads-remote** version (React-Query `useQuery`, same host that serves
the proven SALES/INVENTORY/ads pulls), while the `brand-analytics-web/api/v1/geo-analytics/*`
set is the **vendor-remote brand-analytics app's** own copy of the identical
scorecards. Both are documented below (they are distinct URLs the code actually
calls); a read-only CLI would pick one family per route.

## SPA route(s)

- `/dashboard/geo-insights` · `/vendor/dashboard/geo-insights` — **Geo Insights** map
  dashboard (hyperlocal city/store/product performance, geofence, store locations).
- `/dashboard/market-share` · `/vendor/dashboard/market-share` — **Market Share**
  dashboard (GMV & units share, share-of-voice, top-of-search, new-user %).
- `/elasticity` · `/vendor/elasticity` — **Elasticity** dashboard (price↔volume,
  discount-ROI, pack-size, shopper-clock, trial-to-loyalty, inventory-pulse).
- `/persona` · `/vendor/persona` — **Persona** dashboard (segments, overview,
  city-data, heat-maps, graph configs/data).

The `/vendor/*`-prefixed routes are the vendor-remote (635) mounts of the same four
dashboards; the bare routes are the ads-remote (632) / root-shell mounts.

## Backend host(s)

- **`fcc.zepto.co.in`** — the vendor-reports + ads-bff + brand-analytics host (same
  host the proven SALES / INVENTORY `fcc /api/v1/reports*` and ads `fcc /ads-bff/api/v1`
  pulls use). Three path families on this host serve this section:
  - `api/v1/geo-analytics/*` and `ads-bff/api/v1/coordinates/decode` — ads-remote geo
    dashboard (React-Query GET reads).
  - `brand-analytics-web/api/v1/geo-analytics/*` — vendor-remote copy of the geo
    scorecards.
  - `brand-analytics-web/api/v1/{market-share,elasticity,persona}/*` — market-share,
    elasticity and persona analytics.

## API endpoints (READ)

Every endpoint in this section is a **pure read** (analytics data fetch keyed by
`manufacturerId` + date range; no state change). Method shown as wired in the chunk:
`GET` = confirmed constant/`method:"GET"` binding; `UNKNOWN (read)` = URL constant
present but the verb was not directly emitted next to the string in this chunk (these
are the brand-analytics-app data fetches routed through that chunk's HTTP helper,
whose only non-GET calls are the auth POSTs — so their effect is a read; verb to
confirm on a live capture).

### Geo Insights — ads-remote (`api/v1/geo-analytics/*`, `ads-bff`)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/api/v1/geo-analytics/city-level-performance` | Hyperlocal city-level performance (`GI_GET_HYPERLOCAL_CITY_PERFORMANCE`) | READ |
| GET | `/api/v1/geo-analytics/store-level-performance` | Hyperlocal store-level performance (`GI_GET_HYPERLOCAL_STORE_PERFORMANCE`) | READ |
| GET | `/api/v1/geo-analytics/product-level-performance` | Hyperlocal product-level performance (`GI_GET_HYPERLOCAL_PRODUCT_PERFORMANCE`) | READ |
| GET | `/api/v1/geo-analytics/store-metrics` | Per-store metrics for the map (`GI_GET_HYPERLOCAL_STORE_METRICS`) | READ |
| GET | `/api/v1/geo-analytics/store-locations` | Store point locations for the map (`GI_GET_GEO_ANALYTICS_STORE_LOCATIONS`) | READ |
| GET | `/api/v1/geo-analytics/store-geofence` | Store geofence polygons (`GI_GET_GEO_ANALYTICS_STORE_GEOFENCE`) | READ |
| GET | `/api/v1/geo-analytics/sales-scorecard` | Sales scorecard tiles (`GI_GET_GEO_ANALYTICS_SALES_SCORECARD`) | READ |
| GET | `/api/v1/geo-analytics/fulfillment-scorecard` | Fulfilment scorecard tiles (`GI_GET_GEO_ANALYTICS_FULFILLMENT_SCORECARD`) | READ |
| GET | `/api/v1/geo-analytics/hyperlocal-insights-card` | Hyperlocal insights summary card (`GI_GET_HYPERLOCAL_INSIGHTS_CARD`) | READ |
| GET | `/api/v1/geo-analytics/slider-data` | Time-slider series data for the map (`GI_GET_SLIDER_DATA`) | READ |
| UNKNOWN (read) | `/ads-bff/api/v1/coordinates/decode` | Decode a lat/long into a location/address for the map (`GET_LOCATION_DETAILS`; called via `useQuery` with `params:{url}`, `skipErrorInterceptor` — a lookup, no state change) | READ |

### Geo Insights — vendor-remote copy (`brand-analytics-web/api/v1/geo-analytics/*`)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/city-level-performance` | City-level performance (brand-analytics app copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/store-level-performance` | Store-level performance (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/product-level-performance` | Product-level performance (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/store-metrics` | Per-store metrics (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/store-locations` | Store locations (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/store-geofence` | Store geofence polygons (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/sales-scorecard` | Sales scorecard tiles (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/fulfillment-scorecard` | Fulfilment scorecard tiles (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/hyperlocal-insights-card` | Hyperlocal insights card (copy) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/geo-analytics/slider-data` | Time-slider series data (copy) | READ |

### Market Share (`brand-analytics-web/api/v1/market-share/*`)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/brand-analytics-web/api/v1/market-share/gmv-and-units` | GMV & units market-share vs category (`MARKET_SHARE_GET_MARKET_SHARE_GMV_AND_UNITS`) | READ |
| GET | `/brand-analytics-web/api/v1/market-share/share-of-voice` | Share-of-voice (ad/search visibility) (`MARKET_SHARE_GET_SHARE_OF_VOICE`) | READ |
| GET | `/brand-analytics-web/api/v1/market-share/top-of-search` | Top-of-search ranking share (`MARKET_SHARE_GET_TOP_OF_SEARCH`) | READ |
| GET | `/brand-analytics-web/api/v1/market-share/get-new-users-percentage` | New-users % penetration (`MARKET_SHARE_GET_NEW_USERS_PERCENTAGE`) — probed → **401 Token expired** (documented, expired-token) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/market-share/calculate-bill-penetration` | Bill-penetration computation for the share dashboard (`MARKET_SHARE_CALCULATE_BILL_PENETRATION`; a server-side analytics calc that returns a metric — no state change) | READ |

### Elasticity (`brand-analytics-web/api/v1/elasticity/*`)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN (read) | `/brand-analytics-web/api/v1/elasticity/price-volume` | Price↔volume elasticity curve (const `Ye`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/elasticity/discount-roi` | Discount-ROI curve (const `Ke`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/elasticity/inventory-pulse` | Inventory-pulse series (const `$e`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/elasticity/pack-size-over-time` | Pack-size mix over time (const `We`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/elasticity/shopper-clock` | Shopper-clock (order-time distribution) (const `ze`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/elasticity/trial-to-loyalty` | Trial→loyalty conversion curve (const `Xe`) | READ |

### Persona (`brand-analytics-web/api/v1/persona/*`)

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| UNKNOWN (read) | `/brand-analytics-web/api/v1/persona/overview` | Persona overview cards (const `Ce`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/persona/list` | List of consumer personas/segments (const `fe`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/persona/city-data` | Per-city persona split (const `De`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/persona/graph-configs` | Chart/graph configuration for the persona view (const `Le`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/persona/graph-data` | Persona graph series data (const `ge`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/persona/heat-map` | Persona heat-map (const `he`) | READ |
| UNKNOWN (read) | `/brand-analytics-web/api/v1/persona/heat-map-basket-l3-category` | Basket L3-category heat-map (const `be`) | READ |

## Out of scope (writes) — none in this section

There are **no write, upload, export or report-generation endpoints in this
section** — the entire Market/Geo/Consumer surface is analytics-read. The two
verb-flavoured names are still pure reads and are held **in** scope above:
`coordinates/decode` is a lat/long→address lookup (`GET_LOCATION_DETAILS`, called via
`useQuery`), and `market-share/calculate-bill-penetration` is a server-side analytics
computation that returns a metric — neither mutates Zepto state. (Bulk CSV/Excel of
these dashboards, if any, is minted through the shared vendor-reports queue documented
under [[Vendor-Reports-Queue]], not from this section.)

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first
  401/403/429). `GET https://fcc.zepto.co.in/brand-analytics-web/api/v1/market-share/get-new-users-percentage`
  (const `MARKET_SHARE_GET_NEW_USERS_PERCENTAGE`, a clean pure-GET "get/user" read)
  with the captured vendor JWT returned **`HTTP 401 {"message":"Token
  expired","code":401}`** — the token (`exp 1783967399` = 2026-07-13 18:29:59 UTC,
  `sub 5116e7a0-…`, `ecom1@jivo.in`) had lapsed ~11 days before this run (2026-07-24).
  No 2xx, so **nothing was upgraded to PROVEN**; all endpoints remain **documented
  (not probed)**. Transcript: `captures/ads/market-geo-consumer-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on the same host: SALES /
  INVENTORY (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the
  identical `authorization: <jwt>` header (no `Bearer`), origin/referer
  `https://brands.zepto.co.in`. Re-run these probes with a fresh token — the reads
  additionally need `manufacturerId` + `startDate`/`endDate` query params (confirmed
  wired in `vendor/3539.…js`) to return a 2xx body.
- **Response shapes:** to confirm via live read-only capture. Expected (from the
  dashboard usage): geo `*-performance`/`*-scorecard` → keyed metric arrays per
  city/store/product; `store-locations`/`store-geofence` → geo point/polygon lists;
  `market-share/*` → share %, GMV, units vs category; `elasticity/*` → x/y series for
  each curve; `persona/*` → segment records + heat-map matrices.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing analytics (every endpoint here is already a read):

- `zepto geo city|store|product --from --to` → `api/v1/geo-analytics/{city,store,product}-level-performance`.
- `zepto geo scorecard sales|fulfilment --from --to` → `geo-analytics/{sales,fulfillment}-scorecard`.
- `zepto geo map --from --to` → `store-locations` + `store-geofence` + `store-metrics` + `slider-data` (+ `coordinates/decode` for reverse-geocode).
- `zepto market-share gmv|voice|top-search|new-users --from --to` → `market-share/*`.
- `zepto elasticity price-volume|discount-roi|pack-size|shopper-clock|trial-loyalty|inventory-pulse --from --to` → `elasticity/*`.
- `zepto persona overview|list|cities|heatmap --from --to` → `persona/*`.
- **Excluded:** nothing to exclude for writes — but the CLI must still **consume** a
  token obtained out-of-band and only issue GETs; it must never call the shared
  vendor-reports **generate** endpoints ([[Vendor-Reports-Queue]]) to materialise these as
  files.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Tightest sibling** — [[Brand-Analytics]] (Sales, Live & Landing): same
  `brand-analytics-web` app, same `manufacturerId` + date-range idiom; this note is
  the market/geo/consumer half, that note is the sales/live/landing half of the same
  dashboard shell.
- Adjacent ads surfaces that share the ads remote (632) + `ads-bff` host:
  [[Ads-Campaigns-Booking-Keywords]] · [[Brand-Analytics]] · [[Ads-Billing-Wallet]].
- Bulk CSV/Excel of any dashboard, if minted, rides the shared queue in
  [[Vendor-Reports-Queue]]. The JWT that authenticates every call here is minted in
  [[Auth-Identity]].
