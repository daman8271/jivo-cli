---
title: Brands & Audiences
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, ads, brands-audiences]
status: studied
---

# Brands & Audiences

The **Brands & Audiences** section is the ads-lane's **brand roster + audience-builder** surface: it enumerates the brands/parent-brands an advertiser controls, their sub-categories and L3 targeting categories, the approver/user list behind each parent brand, the per-brand **audience attributes** an advertiser can slice on, the **audience-reach estimate** for a given definition, and the **saved-audience** presets — and it feeds the brand-level analytics header/summary/tabular metrics that the Brand-Analytics dashboards render. For JIVO this is Jivo Wellness Pvt. Ltd. (Manufacturer, STANDARD tier, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`), ads brand **Jivo** `brand_id b3550d5d-fc71-47b0-af4f-f221f909b936`, login `ecom1@jivo.in` (role "External Super Ads Admin"). Every call hits the **ads-BFF mounted on `fcc.zepto.co.in`** (constants are built with the `ads-bff/api/v1/...` prefix; a handful of the analytics-detail constants are stored bare `/api/v1/...` and get the ads-bff base prepended at call time). Auth is the single Zepto JWT in the `authorization` header (no `Bearer` prefix), same token that works across every Zepto backend. Endpoint contracts below were extracted from the ads/root-shell webpack chunks (`root-shell-main.8a3af4e6aebe630f.js` and the code-split `1183.8940422c8268d8dc.js`) — they are the API-constant bindings (`GET_*` / getter functions), **not** live captures (see the probe note under Evidence).

## SPA routes

- `/ads/brand-analytics` — brand-analytics landing (brand + audience context header).
- `/ads/brand-analytics/overview` — brand overview (summary/metrics tiles).
- `/ads/brand-analytics/details` — brand detail (tabular metrics, per-brand drill-down).
- `/vendor-brand-map` — vendor ↔ brand mapping (which vendor codes map to which ads brand).
- `/vendor/vendor-brand-map` — same map under the vendor shell namespace.

## Backend hosts

- `fcc.zepto.co.in` — ads-BFF (`/ads-bff/api/v1/...`); the only host this section talks to. One JWT (`authorization: <jwt>`, no `Bearer`) authorizes it; WAF headers were not enforced at last verified capture (a probe on 2026-07-23 with an already-expired token returned HTTP 429 — see Evidence).

## What the section exposes (concepts)

- **Brands & parent-brands** — flat brand list (`GET_BRANDS_LIST_DATA`), parent-brand list + single parent-brand + the users/approver-email options under a parent brand.
- **Category taxonomy** — sub-categories (`GET_SUBCATEGOEIES_LIST`) and L3 targeting-options (`GET_BRAND_CATEGORIES` / `GET_L3_CATEGORY_LIST`) used to scope audiences and campaigns.
- **Audience builder** — per-brand audience **attributes / section UI**, a **reach estimate** for a candidate audience, **audience-reach (non-endemic)**, and **saved-audience** presets. (Persisting a new audience is a **write** — held out of scope below.)
- **Brand-insight** — layout/section metadata, onboarding state, and per-section chart data for the insight panels; per-brand **smart-nudges**.
- **Brand analytics** — header metadata, summary, metrics + tabular metrics (brand-level and campaign-level) that back the `/ads/brand-analytics` dashboards. (Analytics **report download** is an export — out of scope.)

## READ endpoints

Base = `https://fcc.zepto.co.in/` + path. Paths shown as stored in the bundle; constants (`GET_*` / getter fn) are given for traceability. `${e}` = a brand / parent-brand id (for JIVO, brand `b3550d5d-fc71-47b0-af4f-f221f909b936`). Method column: `GET` = declared GET in the chunk; `GET?` = getter-shaped constant, verb not directly observed (several list/estimate endpoints are POST-with-body but are **pure reads**, same idiom as the vendor-side `report-requests` list). None probed live (token expired at capture; all remain **documented, not probed**).

| METHOD | Path | Purpose (const) | Read/Write |
|---|---|---|---|
| GET | `/ads-bff/api/v1/brands` | Brands list (`GET_BRANDS_LIST_DATA` / `BRANDS_LIST`) | READ |
| GET | `/ads-bff/api/v1/brands/subcategory` | Sub-categories list (`GET_SUBCATEGOEIES_LIST`) | READ |
| GET | `/ads-bff/api/v1/brands/targeting-options` | L3 targeting categories (`GET_BRAND_CATEGORIES` / `GET_L3_CATEGORY_LIST`) | READ |
| GET | `/ads-bff/api/v1/parent-brand` | Parent-brands list (`GET_PARENT_BRANDS_LIST`) | READ |
| GET? | `/ads-bff/api/v1/parent-brand/${e}` | Single parent-brand (`getParentBrand`) | READ |
| GET | `/ads-bff/api/v1/parent-brand/${e}/users` | Users / approver-email options under a parent brand (`getApproverEmailOptions`) | READ |
| GET? | `/ads-bff/api/v1/brand-insight/metadata` | Brand-insight layout/section metadata (`GET_LAYOUT_SECTION_METADATA`) | READ |
| GET? | `/ads-bff/api/v1/brand-insight/onboarding` | Brand-insight onboarding state (`GET_BRANDS_INSIGHTS`) | READ |
| GET? | `/ads-bff/api/v1/brand-insight/section/${e}/data` | Per-section chart data (`getChartData`) | READ |
| GET? | `/ads-bff/api/v1/brand/${e}/smart-nudges` | Smart-nudges for a brand (`getSmartNudges`) | READ |
| GET? | `/ads-bff/api/v1/brands/${e}` | Brand details (`getBrandDetails`) | READ |
| GET? | `/ads-bff/api/v1/brands/${e}/audience-reach` | Audience reach, non-endemic (`GET_AUDIENCE_REACH_NE`) | READ |
| GET? | `/ads-bff/api/v1/brands/${e}/audience/attributes` | Audience attributes / section UI (`GET_AUDIENCE_SECTION_UI`) | READ |
| GET? | `/ads-bff/api/v1/brands/${e}/audience/estimate` | Audience-reach estimate for a definition (`GET_AUDIENCE_REACH`; may be POST-with-body, pure read) | READ |
| GET? | `/ads-bff/api/v1/brands/${e}/saved-audiences` | Saved-audience preset options (`GET_SAVED_AUDIENCE_OPTIONS`) | READ |
| GET | `/api/v1/brands/analytics/metadata` | Analytics header metadata (`GET_HEADERS_DATA`) | READ |
| GET? | `/api/v1/brands/analytics/metrics` | Brand analytics metrics (`GET_BRAND_METRICS`) | READ |
| GET? | `/api/v1/brands/analytics/metrics/tabular` | Brand analytics tabular data (`GET_BRAND_TABULAR_DATA`) | READ |
| GET? | `/api/v1/brands/analytics/summary` | Analytics detail-tab summary (`DETAILS_TAB_SUMMARY`) | READ |
| GET? | `/api/v1/brands/approvers/${e}` | Approver emails for a brand (`getApproversEmails`) | READ |
| GET? | `/api/v1/brands/campaigns/analytics/metadata` | Campaign analytics metadata (`GET_CAMPAIGN_METRICS_DATA`) | READ |
| GET? | `/api/v1/brands/campaigns/analytics/metrics` | Campaign analytics metrics (`GET_CAMPAIGN_METRICS`) | READ |
| GET? | `/api/v1/brands/campaigns/analytics/metrics/tabular` | Campaign analytics tabular data (`GET_CAMPAIGN_TABULAR_DATA`) | READ |
| GET? | `/api/v1/brands` | Brands list, alt constant object (`BRANDS_LIST`; = `ads-bff/api/v1/brands`) | READ |
| GET? | `/api/v1/brands/subcategory` | Sub-categories, alt constant object (`GET_SUBCATEGOEIES_LIST`) | READ |
| GET? | `/api/v1/brands/targeting-options` | L3 categories, alt constant object (`GET_L3_CATEGORY_LIST`) | READ |

## Out of scope (writes / exports) — never expose in a read-only CLI

| METHOD | Path | Purpose (const) | Class |
|---|---|---|---|
| POST | `/ads-bff/api/v1/brands/${e}/audiences` | **Save / create** a custom audience for a brand (`postSaveAudience`) — persists a new audience definition | WRITE |
| GET/POST? | `/ads-bff/api/v1/brands/analytics/reports` | **Download / generate** brand-analytics metrics export (`DOWNLOAD_ANALYTICS_METRICS`) — report-generation/export | EXPORT |
| GET/POST? | `/ads-bff/api/v1/brands/reports` | Wallet-transactions **report download** surfaced under brands (`WALLET_TRANSACTIONS_DOWNLOAD`) — export | EXPORT |

These are held out of scope per [[Read-Only-Guardrails]]: the audience save mutates ads state, and the two `*/reports` endpoints are download/generate exports (`DOWNLOAD_*` / `*_DOWNLOAD` constants) whose verb is unconfirmed — a strict read-only CLI must not fire them.

## Evidence

- **Endpoint set** extracted from webpack module-federation chunks under the ads / root-shell remotes: `root-shell-main.8a3af4e6aebe630f.js` (+ `remoteEntry.js`, `root-shell-styles.*.js`) for the top-level `GET_BRANDS_LIST_DATA` / `GET_SUBCATEGOEIES_LIST` constants, and the code-split **`1183.8940422c8268d8dc.js`** for the audience-builder + analytics constant objects (`GET_AUDIENCE_REACH`, `GET_SAVED_AUDIENCE_OPTIONS`, `GET_HEADERS_DATA`, `DETAILS_TAB_SUMMARY`, `getBrandDetails`, `getParentBrand`, `postSaveAudience`, `DOWNLOAD_ANALYTICS_METRICS`, `WALLET_TRANSACTIONS_DOWNLOAD`, …). Source of truth = the JS corpus on disk.
- **Live probe (read-only, halted):** on 2026-07-23 a single `GET https://fcc.zepto.co.in/ads-bff/api/v1/brands` was fired with the only available JWT (`ecom1@jivo.in`, `exp 2026-07-13 18:29:59 UTC` — **expired**). Response = **HTTP 429**. Per the guardrail (stop on any 401/403/429), probing halted immediately; **no endpoint upgraded to PROVEN**, all remain **documented (not probed)**. Transcript: `captures/ads/brands-audiences-probes.txt`.
- **Request/response bodies uncaptured** — no `captures/ads/*.json` exists for any brands/audience endpoint yet; exact filter keys, the audience-attribute schema, and the estimate request body want a live (read-only) capture with a fresh token to finalise.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no audience save, no report/export generation):

- `zepto brands list` → `GET /ads-bff/api/v1/brands`; `zepto brands parents` → `parent-brand`; `zepto brands parent <id>` + `zepto brands parent <id> users`.
- `zepto brands subcategories` → `brands/subcategory`; `zepto brands targeting` → `brands/targeting-options` (L3 categories).
- `zepto brands get <brandId>` → `brands/${e}`; `zepto brands approvers <brandId>` → `brands/approvers/${e}`.
- `zepto audience attributes <brandId>` → `brands/${e}/audience/attributes`; `zepto audience saved <brandId>` → `brands/${e}/saved-audiences`; `zepto audience reach <brandId>` → `brands/${e}/audience-reach` / `audience/estimate` (read-only estimate).
- `zepto brands insight metadata|onboarding|section <id>` → `brand-insight/*`; `zepto brands nudges <brandId>` → `brand/${e}/smart-nudges`.
- `zepto brands analytics metadata|summary|metrics|tabular` → `brands/analytics/*`; campaign variants → `brands/campaigns/analytics/*`.

Explicitly **excluded**: `postSaveAudience` (create audience), `DOWNLOAD_ANALYTICS_METRICS`, and `WALLET_TRANSACTIONS_DOWNLOAD` (export/report-generation).

## Connections

- Index & shared refs: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- **Tightest siblings** (same ads BFF): brand-level metrics rendered by [[Brand-Analytics]]; audiences drive creatives in [[Creative-Management]] and targeting in [[Ads-Campaigns-Booking-Keywords]]; wallet-transactions export overlaps [[Ads-Billing-Wallet]]; audience geo/consumer overlays in [[Market-Geo-Consumer-Insights]] and [[Engagement]].
- Approver/user lists tie back to platform identity: [[Users-Access]].
