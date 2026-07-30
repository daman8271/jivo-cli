---
title: Flipkart-Ads-and-FSN
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, ads, read-only]
status: studied
---

# Flipkart-Ads-and-FSN

> ⚠️ READ-ONLY. Flipkart Ads (PLA/PCA campaigns via fed-ads) + Consolidated FSN performance + fkpromo.

**Endpoints in this section:** 20 — 5 read-safe (READ/READ_FILE), 4 write/export (out of scope), 11 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-darkstore-discount` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-eligible-listings` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-managed-listings` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-mapped-listings` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-recommended-listings` | downloadRecommendedFileApi | READ_FILE |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/delete-managed-listings` | deleteManagedFileApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-update-listings` | updateManagedFileApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-upload-post-opt-in` | uploadManagedFilePostOptInApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/upload-selsub-listings` | uploadManagedFileApi | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/fed-ads/navbar/seller` | — |
| UNKNOWN | `seller.flipkart.com/fed-ads/sellerpoc` | — |
| UNKNOWN | `seller.flipkart.com/fed-ads/violet-lms/authenticate` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-file-validation-status` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-file-validation-status-V3` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-opt-in` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-opt-in-mandate` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-opt-out` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-retry-validation` | retryApi |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/get-fk-promotion-by-id` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkpromo/get-fk-promotions` | — |

## PROVEN detail & what JIVO uses this for

Flipkart Ads lives on a **separate service** `seller.flipkart.com/fed-ads/*` (not `/napi/`), same
cookie jar + CSRF plus `x-aaccount`/`x-baccount` = sellerId, `x-tenant: SELLER`. Both endpoints are
**POSTs that return a CSV synchronously** — and both **create/serve an export**, so they are
classed EXPORT and were **never fired** by this study.

| Verb | Path | Proven result (JIVO, 2026-07-08) | Posture |
|---|---|---|---|
| POST | `fed-ads/downloadV2` | 23,301 B CSV, **260 campaign rows** | EXPORT (campaign-level) |
| POST | `fed-ads/download/table` | 46,140 B CSV, **269 product rows** (needs `x-pagecontext: …#PLA#sellerPlaConsolidatedFSNReport#csv`) | EXPORT (FSN/product-level) |

**Ads campaign fields (17):** `id, name, status, type, marketplace, startAndEndDate, budget,
budgetType, cost, remainingBudget, views, clicks, totalConvertedUnits, totalConvertedRevenue, roi,
ctr, cvr`.
**Ads request dimensions:** `type` = `PLA` / `SELLER_PCA`; `marketplace` = `FLIPKART` / `SHOPSY`;
`budgetType` = `DAILY_BUDGET` / `TOTAL_BUDGET`; `timeGranularity` = `DAY`; `isRealTime: true`.
**FSN report:** `reportId=sellerPlaConsolidatedFSNReport`, `view_id=612`, group-by
`campaign_id, campaign_name, ad_group_id, ad_group_name, sku_id, listing_name`; metrics
`views, engagements, direct_units, indirect_units, total_revenue, cvr, roi, cost`.

**Live count (UNVERIFIED-today):** 260 ad campaigns, 269 FSN rows as of JIVO's July pull. Re-pulling
today requires the app to POST during a live walk (not run this session) — the CSV export cannot be
fetched by a GET-only replay without authoring a POST (forbidden). See [[Flipkart-Data-Inventory]] §3.
`view_id=612` + `reportId` are the keys into a wider fed-ads report catalogue — more report ids
almost certainly exist than the one JIVO pulls (PENDING_AUTH enumeration).

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
