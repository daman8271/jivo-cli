---
title: Vendor-Analytics
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Analytics

> ⚠️ READ-ONLY. Sales & inventory analytics: aggregated metrics, purchasing trends, operational performance, product details.

**Endpoints in this section:** 7 — 2 read-safe (READ/READ_FILE), 2 write/export (out of scope), 3 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/operational-performance` | updateApi | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/purchasing-trends` | updateApi | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/report` | — | EXPORT |
| UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/sales-report` | — | EXPORT |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/aggregated-metrics` | — |
| UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/filter-data` | — |
| UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/product-details` | fetchApi |

## PROVEN detail & what JIVO uses this for

**Live reads (GET, 200 this session):** `vendor/config/sale-config` → `{isSaleActive:false,
startDate:2025-09-22, endDate:2025-10-03}`; `vendor/cataloging/browse-tree` → 130 KB category tree.
`aggregate-entities`, `operational-performance`, `purchasing-trends` returned `{message}` stubs
(need warehouse/date params — shape PENDING_AUTH).

**JIVO's daily flow (Flow 16, from `~/ecomcliauto`):** the Sales & Inventory analytics reports are
delivered by **enqueue → email/sync-download**, not a live JSON read:
- `POST vendor/analytics/sales-report` `{"filter":{}}` → `{sync:true, document_id:"CONA…"}` (or
  `{}` → async email), then `GET vendor-p/getFile/v1/retail/documents/<document_id>/download` → xlsx.
- `POST vendor/analytics/report` `{"filter":{}, "dateTime":…}` → inventory report (emailed link).

Both POSTs are **EXPORT/enqueue (G2) — never fired here** (Vendor Hub throttles after ~8 triggers/2 h).
The **`getFile/.../download`** GET is the read-safe terminal step (documented in [[Vendor-Documents]]).

**Sales report shape (JIVO-VERIFIED, July):** wide pivot — rows = FSN (`Tenant ID, Retailer ID,
Retailer Name, FSN, CATEGORY, VERTICAL, BRAND`) × one column per day (~30–60 days). **Inventory
report** adds `Warehouse, Inventory Available Units/Value, Rate of Sale 30/60/90d, Estimated DOH,
Inventory Health, Sell-Through Rate, Aging, HSN, EAN, …`.

**Live (VERIFIED via walk, `sec-09`/`sec-10` in [[Flipkart-Live-Walk]]):** the Sales & Inventory
Analytics → Product Details page enumerates **319 FK warehouses** in its filter (del_/mum_/noi_/ghz_…),
default filter "Fast Selling & Low DOH (<10 days)", category **Gourmet**; tabs Product Catalog /
Stock Information / Sales & Inventory Analytics / Legal Metrology Non-Compliance. Per-SKU inventory
rows load behind those filters. Other 8 vendors PENDING_AUTH (vendor switch). See [[Flipkart-Data-Inventory]].

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
