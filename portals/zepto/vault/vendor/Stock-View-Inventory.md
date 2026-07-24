---
title: Stock View & Inventory
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, vendor, stock-inventory]
---

# Stock View & Inventory

The **Stock View & Inventory** section is Zepto's **on-shelf availability + on-hand stock analytics** surface for a brand/vendor. It answers two questions JIVO (Jivo Wellness Pvt. Ltd., Manufacturer, `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`) cares about across Zepto's dark-store network: **"is my SKU actually available to buy?"** (Availability tab) and **"how much of my stock is sitting in Zepto?"** (Inventory tab). Each tab renders headline metric tiles plus three drill-downs — **city-wise**, **store-wise**, and **product/SKU-wise** — filtered by SKU codes, Brand, Category and a date window. Everything is a **pure read**: the page fetches metrics and grids, it changes no state.

It is the analytics counterpart to the raw-file lane: the existing `zepto-cli` already pulls a flat **INVENTORY report** via the FCC reports queue (`fcc /api/v1/reports*`, see [[Vendor-Reports-Queue]]); this section is the **interactive brand-analytics** view of the same on-hand/availability data, served by the `brand-analytics-web` backend (the same backend behind [[Brand-Analytics]]). The endpoint contracts below were extracted from the vendor micro-frontend chunks `vendor/3539.64ab07c46b8741b5.js` (path constants) and `vendor/2696.09270516e3d7a2e1.js` (the `Kp.post({path,data})` caller bindings) — they are code constants, not live captures (no endpoint returned 2xx; see Real data seen).

## SPA routes

- `/stock-view` (and lane-prefixed `/vendor/stock-view`) — the Stock View page: **Availability** + **Inventory** tabs, metric tiles, and the city / store / product grids. SKU filter chip is `sku-stock-view` ("SKU Codes"), plus **Brand** and **Category** filters. Subscription gate flag `STOCK_VIEW_FREE_AVAILABLE_TILL` (`stock_view_free_available_till`) governs the free-trial window; module id `STOCK_VIEW = 4f58dea3-e8ea-451c-8b50-509dd6f700cf`.
- `/reconciliation/inventory` (and `/vendor/reconciliation/inventory`) — the inventory reconciliation route (inventory vs system counts), same backend family.

## Backend host

- `fcc.zepto.co.in` — all 9 endpoints. The 8 Stock View analytics paths carry the `brand-analytics-web/` proxy segment (full URL `https://fcc.zepto.co.in/brand-analytics-web/api/v1/…`; the bifrost gateway routes the `brand-analytics-web` segment to the brand-analytics service — confirmed by probe, see transcript). The 9th is the ads-BFF slot-availability check under `fcc.zepto.co.in/ads-bff/api/v1/…`. Auth = single JWT in the `authorization` header (no `Bearer` prefix), same token that works across every Zepto backend. See [[Auth-and-Access]].

## READ endpoints

Base = `https://fcc.zepto.co.in/` + path. Methods below are **as wired in the bundle** (`Kp.post({path,data})` / `Kp.get({path,params})`). The 8 Stock View endpoints are **POST-with-filters bodies but pure reads** (no state change — same idiom as the analytics list reads elsewhere in this portal); the `data` body carries `{sku codes, brand, category, start_date, end_date, market_place_type, …}` merged from the page filters. None returned 2xx (expired token + a 429), so none are marked PROVEN.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| POST | `brand-analytics-web/api/v1/stock-view/availability/summary` | Availability tab headline metric tiles (`AVAILABILITY.GET_METRICS`, `getMetrics`) | READ |
| POST | `brand-analytics-web/api/v1/stock-view/availability/city-level-performance` | Availability by city (`GET_CITY_WISE_AVAILABILITY_DATA`, `getCityWiseAvailabilityData`) | READ |
| POST | `brand-analytics-web/api/v1/stock-view/availability/store-level-performance` | Availability by dark-store (`GET_STORE_WISE_AVAILABILITY_DATA`, `getStoreWiseAvailabilityData`) | READ |
| POST | `brand-analytics-web/api/v1/stock-view/availability/product-level-performance` | Availability by SKU/product (`GET_PRODUCT_WISE_AVAILABILITY_DATA`, `getProductWiseAvailabilityData`) | READ |
| POST | `brand-analytics-web/api/v1/stock-view/inventory/summary` | Inventory tab headline metric tiles (`INVENTORY.GET_METRICS`) | READ |
| POST | `brand-analytics-web/api/v1/stock-view/inventory/city-level-performance` | On-hand inventory by city (`GET_CITY_WISE_INVENTORY_DATA`) | READ |
| POST | `brand-analytics-web/api/v1/stock-view/inventory/store-level-performance` | On-hand inventory by dark-store (`GET_STORE_WISE_INVENTORY_DATA`) | READ |
| POST | `brand-analytics-web/api/v1/stock-view/inventory/product-level-performance` | On-hand inventory by SKU/product (`GET_PRODUCT_WISE_INVENTORY_DATA`) | READ |
| GET | `ads-bff/api/v1/inventory/availability?inventory_id=&brand_id=&start_date=&end_date=&market_place_type=` | Ads-BFF **ad-slot** inventory availability (`CAMPAIGN_CONFIG.GET_INVENTORY_AVAILABILITY`, `Kp.get`) — belongs to the ads booking flow, bucketed here by path name; returns bookable slot inventory, not vendor stock | READ |

## Out of scope (writes)

**None.** This section is entirely read-only — every endpoint is a metrics/grid fetch. There are no create/update/delete, upload, export, or report-generation endpoints in the Stock View & Inventory bundle. (The flat inventory **file** export lives in the separate reports queue — see [[Vendor-Reports-Queue]] — not here.)

## Real data seen (evidence)

- **Method proof in bundle:** `vendor/2696.09270516e3d7a2e1.js` wires each grid fetch as `A.Kp.post({path:f.S_.AVAILABILITY.GET_METRICS,data:Object.assign({},e)})` (and the matching `INVENTORY.GET_*` set via `c.S_.INVENTORY.*`) — confirming all 8 Stock View calls are POST-with-filters reads. Path constants (`Me/we/Fe/Ve` = availability summary/city/store/product; `Be/je/ke/He` = inventory summary/city/store/product) are grouped under an `{AVAILABILITY:{…}, INVENTORY:{…}}` namespace in `vendor/3539.64ab07c46b8741b5.js`.
- **Ads-BFF GET proof:** `ads/1183.8940422c8268d8dc.js` calls `K.Kp.get({path:…GET_INVENTORY_AVAILABILITY, params:{inventory_id,start_date,market_place_type,end_date,brand_id}})` — a genuine GET, but it is the **ads slot-availability** check (Jivo ads `brand_id b3550d5d-fc71-47b0-af4f-f221f909b936`), not vendor on-hand stock.
- **No live 2xx (nothing PROVEN).** Read-only probes (transcript at `captures/vendor/stock-inventory-probes.txt`): the reused JWT was **expired** (exp 2026-07-13); a GET on `availability/summary` returned bifrost `404 "Api path not found"` (route is POST, GET absent), confirming the `brand-analytics-web/` proxy-segment routing; the one confirmed-GET ads-bff endpoint returned **429** (rate-limit/WAF), which tripped the stop rule. The READ-ONLY LAW also forbids firing the 8 POST endpoints regardless of read-effect, so they were documented from the bundle only.
- **UI filters observed:** SKU-code multiselect (`sku-stock-view`, "SKU Codes"), plus `placeholder:"Brand"` and `placeholder:"Category"` filter chips, feeding the shared filter body; subscription gate `STOCK_VIEW_FREE_AVAILABLE_TILL`.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming metrics/grids (all POST-with-filters, but pure reads):

- `zepto stock availability summary [--sku … --brand … --category … --from --to]` → `POST …/stock-view/availability/summary`.
- `zepto stock availability by city|store|product [same filters]` → the three `availability/*-level-performance` grids.
- `zepto stock inventory summary [same filters]` → `POST …/stock-view/inventory/summary`.
- `zepto stock inventory by city|store|product [same filters]` → the three `inventory/*-level-performance` grids.
- (Ads slot availability — `ads-bff/inventory/availability` — is really an ads-campaign read; belongs under an `ads` command group, not vendor stock.)

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- **Tightest siblings:** the flat inventory-file export of the same data → [[Vendor-Reports-Queue]] (`fcc /api/v1/reports*`, already pulled by `zepto-cli`); the shared `brand-analytics-web` backend & analytics idiom → [[Brand-Analytics]]; the SKUs whose availability this measures → [[Catalog-Health]]; upstream demand that drives stock → [[Purchase-Orders]].
