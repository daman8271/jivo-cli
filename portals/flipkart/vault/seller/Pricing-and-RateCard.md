---
title: Pricing-and-RateCard
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Pricing-and-RateCard

> ⚠️ READ-ONLY. Price management, price scheduling, rate cards & commission.

**Endpoints in this section:** 20 — 0 read-safe (READ/READ_FILE), 7 write/export (out of scope), 13 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/price-scheduling/priceRuleCreate` | kRe | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/price-scheduling/priceRuleUpdate` | NRe | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/pricing/approvePriceApproval` | approveApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/pricing/createPriceApprovalJob` | createPriceApprovalJob | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/pricing/disapproveApprovedListings` | disapproveApprovedListings | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/pricing/disapprovePriceApproval` | disapproveApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/pricing/updateLPOverride` | updateLPOverride | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/pricing/approvalJobStatus` | getApprovalJobStatus |
| UNKNOWN | `seller.flipkart.com/napi/pricing/pendingPriceApprovals` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalHistory` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalReviewCycle` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalSetThreshold` | postApprovalThresholdApi |
| UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalThresholds` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/pricing/reviewAction` | — |
| UNKNOWN | `seller.flipkart.com/napi/rate-card/fetch-is-shopsy-fsn` | fetchShopsyValidationURL |
| UNKNOWN | `seller.flipkart.com/napi/rate-card/fetchRateCardFees` | customURL |
| UNKNOWN | `seller.flipkart.com/napi/rate-card/get-complete-category-tree` | — |
| UNKNOWN | `seller.flipkart.com/napi/rate-card/getRateCardCategories` | fetchRateCardCategoryURL |
| UNKNOWN | `seller.flipkart.com/napi/rate-card/getRateCardSubCategories` | fetchRateCardSubCategoryURL |
| UNKNOWN | `seller.flipkart.com/napi/welcome/fetch-rate-card-fees` | fetchRateCardFees |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
