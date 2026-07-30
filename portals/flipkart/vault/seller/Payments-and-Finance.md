---
title: Payments-and-Finance
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Payments-and-Finance

> ⚠️ READ-ONLY. Settlements, payments, TDS, partner-master finance data.

**Endpoints in this section:** 36 — 19 read-safe (READ/READ_FILE), 16 write/export (out of scope), 1 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/partner-master/categories` | GET_CATEGORIES | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/ads` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/banner` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/feedback/factors/` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/feedback/ratings/` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/partner_categories` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/partners/summary` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/quotation/` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/quotes` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/service-orchestration/document/list` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/partner_categories/list` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/seller` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/unrated/seller/` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/{quote_id}/seller/audit` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/{quote_id}/seller/status` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/ratings` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/ratings/reviews` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v2/quotes/seller` | — | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v2/quotes/seller/cta` | — | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/metrics-rest/category-mandate/settlement-file/initiate` | — | WRITE |
| GET | `seller.flipkart.com/napi/metrics-rest/category-mandate/settlement-file/poll` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics-rest/settlement-template-upload/` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics-rest/settlement-updated-file-upload/` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/payments-rest/photoView` | PHOTO_VIEW_ENDPOINT | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/payments-rest/uploadSpfClaimFile` | — | WRITE |
| GET | `seller.flipkart.com/napi/payments/checkFyReportAvailableV2` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/payments/downloadSellerStatements` | — | WRITE |
| GET | `seller.flipkart.com/napi/payments/fetchBlockStatus` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/payments/fetchLastPaymentDetails` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/payments/fetchOutstandingPaymentDetails` | — | WRITE |
| GET | `seller.flipkart.com/napi/payments/fetchSellerStatement` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/tds/getClaimEligibilty` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/tds/getClaimHistory` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/tds/getTDSClaimData` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/tds/postTdsUploadData` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/manageProfile/getTDSDocument` | fetchApi |

## Live walk findings (VERIFIED 2026-07-30)

From the live Seller Hub Payments → Account Summary (screenshot `sec-12` in [[Flipkart-Live-Walk]]):
**Upcoming Payment ₹3,90,075**; estimate cards ₹19,82,191 / ₹5,33,021 / **₹-8,87,863** / ₹3,97,319.
⚠️ **Payouts are BLOCKED**: banner "your postpaid payment is blocked as you have **Ads dues**… clear
the due amount to unblock your payouts from Flipkart." Sub-nav: Payments Overview · Download
Invoice/Reports · View Order-wise Settlements. (Home tile also flags **Upcoming Payment ₹3.9 L Due**.)


## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
