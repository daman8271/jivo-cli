---
title: Brand Analytics (Sales, Live & Landing)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, ads, brand-analytics]
status: studied
---

# Brand Analytics (Sales, Live & Landing)

The **Brand Analytics** section is the ads-lane's **performance-reporting surface** — the three dashboards a brand reads to see how it is selling on Zepto: **Sales Analytics** (the slow, settled view — revenue, AOV, ASP, offers, product performance over a date range), **Live Monitor** (the fast, near-real-time view — impressions, orders, conversion of the current window), and the **Landing Page** (the top-of-funnel roll-up — header KPIs, AOV, bill penetration, product performance, sub-category heatmap, top-searched keywords). It also surfaces the **fulfilment SLA** tiles (fill-rate, on-time-in-full, available-in-service-hours) and the **subscription/plan gating** that decides which analytics a STANDARD-tier brand can see. For JIVO this is Jivo Wellness Pvt. Ltd. (Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`), ads brand **Jivo** `brand_id b3550d5d-fc71-47b0-af4f-f221f909b936`, login `ecom1@jivo.in`. Every call hits **`fcc.zepto.co.in`** under one of three path namespaces — `brand-analytics-web/api/v1/...` (desktop), `brand-analytics-mobile/api/v1/...` (the mobile app), and a set of bare `api/v1/landing-page/...` / `api/v1/filter|commons/...` constants that get their base prepended at call time. Auth is the single Zepto JWT in the `authorization` header (no `Bearer` prefix), same token that works across every Zepto backend. Endpoint contracts below were extracted from the webpack chunks — the code-split vendor chunk **`3539.64ab07c46b8741b5.js`** (the analytics dashboards) and the root-shell federation chunks (`remoteEntry.js`, `root-shell-main.8a3af4e6aebe630f.js`, `root-shell-styles.1e0d8621a83c83fb.js`) for the mobile subscription/access constants — they are the API-constant bindings (`GET_*` / getter functions / bare path strings), **not** live captures (see the probe note under Evidence).

## SPA routes

- `/ads/analytics` — ads-lane Brand Analytics entry (landing-page roll-up + tab switch to Sales / Live).
- `/dashboard/sales-analytics` · `/vendor/dashboard/sales-analytics` — Sales Analytics dashboard (settled revenue/AOV/ASP/offers/product-performance), under both the ads shell and the vendor shell namespace.
- `/dashboard/live-monitor` · `/vendor/dashboard/live-monitor` — Live Monitor dashboard (near-real-time impressions/orders/conversion).
- `/sales-overview/details` — Sales overview drill-down (the `sales-analytics/sales-overview` detail view).
- `/messages/mark_as_delivered` · `/sdk/push_delivery` — **not** navigable analytics screens; these are Firebase Cloud Messaging service-worker paths that ride in the same bundle (push-notification delivery receipts), listed here only because they appear alongside the section's route set. No brand-analytics API is served from them.

## Backend hosts

- `fcc.zepto.co.in` — the only host this section talks to. Three path namespaces on it: `brand-analytics-web/api/v1/...` (desktop dashboards + fulfilment + resource-last-updated), `brand-analytics-mobile/api/v1/...` (mobile access-management + subscription), and bare `api/v1/landing-page/...` (+ `api/v1/filter/city-list`, `api/v1/commons/brand-category-mapping`) whose base is prepended at call time. One JWT (`authorization: <jwt>`, no `Bearer`) authorizes all of them; WAF headers were not enforced at last verified capture.

## What the section exposes (concepts)

- **Sales Analytics** (settled) — `sales-overview` totals, **average-order-value**, **average-selling-price** per unit, **offers**, and a view-typed **product-performance** table (`getSaProductPerformance` takes a `viewType` query param). Backed by `resource-last-updated` (freshness stamp) and the shared filter constants (`api/v1/filter/city-list`, `api/v1/commons/brand-category-mapping`) for the city / brand-category pickers.
- **Live Monitor** (near-real-time) — `metric-headers` (the KPI header row), **impression-metrics**, **order-metrics**, **conversion-metrics**, and a live **product-list**.
- **Landing Page** (top-of-funnel roll-up) — `header-metrics` (+ a `-lite` variant), **aov**, **bill-penetration**, **product-performance**, **subcategory-heatmap**, **top-searched-keywords**.
- **Fulfilment SLA** — `fill-rate`, `on-time-in-full`, `available-in-service-hours` (the same chunk also references `kyc/average-revenue-per-user` and an `…average-user-penetration` KYC metric string, adjacent constants surfaced on the analytics header).
- **Subscription / plan gating** (mobile) — `subscription/user-details`, `subscription/pricing-details`, `subscription/visibility-details` decide which analytics a plan tier unlocks; `access-management/user` returns the entity/user context for the mobile app.

## READ endpoints

Base = `https://fcc.zepto.co.in/` + path. Method column: `GET` = declared GET in the chunk; `GET?` = getter-shaped / bare-path constant, verb not directly observed (several metric/list endpoints are POST-with-body but are **pure reads**, same idiom as the vendor-side `report-requests` list). None probed live (token expired at capture — HTTP 401 "Token expired"; all remain **documented, not probed**). `${e}` where present = a `viewType` / id query arg.

| METHOD | Path | Purpose (const) | Read/Write |
|---|---|---|---|
| GET? | `/api/v1/landing-page/header-metrics` | Landing header KPI tiles (`J`) | READ |
| GET? | `/api/v1/landing-page/header-metrics-lite` | Landing header KPIs, lite variant (`ee`) | READ |
| GET? | `/api/v1/landing-page/aov` | Landing average-order-value tile (`te`) | READ |
| GET? | `/api/v1/landing-page/bill-penetration` | Landing bill-penetration metric (`ae`) | READ |
| GET? | `/api/v1/landing-page/product-performance` | Landing product-performance table (`ne`) | READ |
| GET? | `/api/v1/landing-page/subcategory-heatmap` | Landing sub-category heatmap (`se`) | READ |
| GET? | `/api/v1/landing-page/top-searched-keywords` | Landing top-searched keywords (`ie`) | READ |
| GET? | `/brand-analytics-web/api/v1/live-analytics/metric-headers` | Live Monitor KPI header row (`W`) | READ |
| GET? | `/brand-analytics-web/api/v1/live-analytics/impression-metrics` | Live impressions (`Z`) | READ |
| GET? | `/brand-analytics-web/api/v1/live-analytics/order-metrics` | Live orders (`z`) | READ |
| GET? | `/brand-analytics-web/api/v1/live-analytics/conversion-metrics` | Live conversion (`q`) | READ |
| GET? | `/brand-analytics-web/api/v1/live-analytics/product-list` | Live per-product list (`Q` / `qe`) | READ |
| GET | `/brand-analytics-web/api/v1/sales-analytics/sales-overview` | Sales overview totals (`SA_GET_SALES_OVERVIEW`) | READ |
| GET | `/brand-analytics-web/api/v1/sales-analytics/average-order-value` | Sales AOV (`SA_GET_AVERAGE_ORDER_VALUE`) | READ |
| GET | `/brand-analytics-web/api/v1/sales-analytics/average-selling-price` | Sales ASP per unit (`SA_GET_AVERAGE_SELLING_PRICE_PER_UNIT`) | READ |
| GET | `/brand-analytics-web/api/v1/sales-analytics/offers` | Sales offers metric (`SA_GET_OFFERS`) | READ |
| GET? | `/brand-analytics-web/api/v1/sales-analytics/product-performance` | Sales product-performance, `?viewType=${e}` (`getSaProductPerformance`) | READ |
| GET | `/brand-analytics-web/api/v1/fulfilment/fill-rate` | Fulfilment fill-rate SLA (`GET_FULFILMENT_FILL_RATE`) | READ |
| GET | `/brand-analytics-web/api/v1/fulfilment/on-time-in-full` | Fulfilment on-time-in-full SLA (`GET_FULFIMENT_ON_TIME_IN_FULL`) | READ |
| GET | `/brand-analytics-web/api/v1/fulfilment/available-in-service-hours` | Fulfilment in-service-hours availability (`GET_FULFILMENT_AVAILBLE_IN_SERVICE_HOURS`) | READ |
| GET | `/brand-analytics-web/api/v1/resource-last-updated` | Data-freshness stamp for the dashboards (`GET_RESOURCE_LAST_UPDATED`) | READ |
| GET | `/brand-analytics-mobile/api/v1/access-management/user` | Mobile entity/user context (`GET_ENTITY_DATA_FOR_MOBILE_APP`) | READ |
| GET | `/brand-analytics-mobile/api/v1/subscription/user-details` | Mobile subscription/plan details (`GET_SUBSCRIPTION_DETAILS_MOBILE`) | READ |
| GET | `/brand-analytics-mobile/api/v1/subscription/pricing-details` | Mobile plan pricing (`GET_PRICING_DETAILS_MOBILE`) | READ |
| GET | `/brand-analytics-mobile/api/v1/subscription/visibility-details` | Mobile plan-visibility gating (`GET_PLAN_VISIBILITY_DETAILS_MOBILE`) | READ |

**Adjacent shared-filter constants** seen in the same chunk (support the pickers above, not standalone section screens): `GET /api/v1/filter/city-list` (`GET_CITY`), `GET /api/v1/commons/brand-category-mapping` (`GET_BRANDS_AND_CATEGORY`), plus KYC metric strings `brand-analytics-web/api/v1/kyc/average-revenue-per-user` (`KYC_GET_REVENUE_PER_USER`) and `…/kyc/average-user-penetration` — all READ; documented here for traceability, primary home is the shared filter/commons layer.

## Out of scope (writes / exports) — never expose in a read-only CLI

| METHOD | Path | Purpose (const) | Class |
|---|---|---|---|
| — | (none in this section) | Brand Analytics is an entirely **read** surface — every constant in `3539.*.js` for this section is a `GET_*` metric/list getter; no create/update/delete or report-generation verb is wired here | — |

This section fires no writes and no exports. The analytics **report-download / export** endpoints (`DOWNLOAD_ANALYTICS_METRICS`, `WALLET_TRANSACTIONS_DOWNLOAD`) live in the sibling [[Brands-Audiences]] note and are held out of scope there per [[Read-Only-Guardrails]]. If a Sales-Analytics "Download" button is later found to call a `…/reports` endpoint, it must be documented as EXPORT and excluded — a strict read-only CLI consumes only the metric getters above.

## Evidence

- **Endpoint set** extracted from the vendor code-split chunk **`3539.64ab07c46b8741b5.js`** (the Sales / Live / Landing dashboards — holds the `SA_GET_*`, `GET_FULFILMENT_*`, `live-analytics/*`, and `landing-page/*` constants plus the `getSaProductPerformance` view-typed getter) and the root-shell federation chunks `remoteEntry.js` / `root-shell-main.8a3af4e6aebe630f.js` / `root-shell-styles.1e0d8621a83c83fb.js` (the `brand-analytics-mobile/api/v1/access-management/user` + `subscription/*` mobile constants). Source of truth = the JS corpus on disk.
- **Live probe (read-only, halted):** on 2026-07-24 a single `GET https://fcc.zepto.co.in/brand-analytics-web/api/v1/access-management/user` was fired with the only available JWT (reused from `captures/vendor/23-sales-list.txt`, `exp 2026-07-13 18:29:59 UTC` — **expired**). Response = **HTTP 401 `{"message":"Token expired","code":401}`**. Per the guardrail (stop on any 401/403/429), probing halted immediately after probe 1; **no endpoint upgraded to PROVEN**, all remain **documented (not probed)**. Transcript: `captures/ads/brand-analytics-probes.txt`.
- **Request/response bodies uncaptured** — no `captures/ads/*.json` exists for any brand-analytics endpoint yet; the exact date-range / city / `viewType` query keys and the metric response schemas want a live (read-only) capture with a fresh `ecom1@jivo.in` token to finalise.
- **Existing coverage:** the zepto-cli already pulls **SALES + INVENTORY** via the vendor `fcc /api/v1/reports*` flow and the ads 2×2 products/brands × range/daily via `fcc /ads-bff/api/v1` — those are the *vendor-report* and *ads-bff* lanes; the `brand-analytics-web/-mobile` dashboards documented here are a **distinct, not-yet-wired** namespace.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing metric getters (no export, no report-generation):

- `zepto analytics sales overview|aov|asp|offers` → `brand-analytics-web/api/v1/sales-analytics/{sales-overview,average-order-value,average-selling-price,offers}`; `zepto analytics sales products [--view <viewType>]` → `sales-analytics/product-performance?viewType=`.
- `zepto analytics live headers|impressions|orders|conversion|products` → `brand-analytics-web/api/v1/live-analytics/{metric-headers,impression-metrics,order-metrics,conversion-metrics,product-list}`.
- `zepto analytics landing headers[--lite]|aov|bill-penetration|products|heatmap|keywords` → `api/v1/landing-page/{header-metrics[-lite],aov,bill-penetration,product-performance,subcategory-heatmap,top-searched-keywords}`.
- `zepto analytics fulfilment fill-rate|otif|in-service` → `brand-analytics-web/api/v1/fulfilment/{fill-rate,on-time-in-full,available-in-service-hours}`.
- `zepto analytics freshness` → `brand-analytics-web/api/v1/resource-last-updated`; `zepto analytics filters cities|categories` → `api/v1/filter/city-list` + `api/v1/commons/brand-category-mapping`.
- `zepto analytics subscription details|pricing|visibility` + `zepto analytics whoami` → `brand-analytics-mobile/api/v1/{subscription/user-details,subscription/pricing-details,subscription/visibility-details,access-management/user}`.

Explicitly **excluded**: any `…/reports` analytics export (belongs to [[Brands-Audiences]] / [[Ads-Billing-Wallet]] out-of-scope), and the FCM `mark_as_delivered` / `push_delivery` service-worker paths (not APIs).

## Connections

- Index & shared refs: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- **Tightest sibling** — [[Brands-Audiences]] renders the brand roster + audience header that these dashboards sit under, and holds the analytics **export** endpoints held out of scope here.
- Sales/inventory settled numbers overlap the vendor-report lane ([[Vendor-Reports-Queue]] · [[Stock-View-Inventory]]); geo/city slicing overlaps [[Market-Geo-Consumer-Insights]]; live impressions/conversion tie to campaign delivery in [[Ads-Campaigns-Booking-Keywords]] and creatives in [[Creative-Management]]; consumer-facing engagement in [[Engagement]].
- Subscription/plan gating ties back to platform billing: [[Subscription-Billing]]; access-management/user context ties to [[Users-Access]] · [[Auth-Identity]].
