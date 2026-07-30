---
title: Listings & ASIN Management
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, listings-asin-management]
status: studied
read_only: true
---

# Listings & ASIN Management

**Portal:** Seller Central (3P) · **Section:** `seller/Listings-ASIN-Management` · **Endpoints catalogued:** 60 (4 read-safe, 3 PROVEN live · 35 out-of-scope · 21 unknown/telemetry)

Add-a-product / edit-listing (ABIS), listing drafts, list-your-products (LYP), and the whole create/clone/variation surface. Nearly all of ABIS is WRITE (create-listing, write-offer, edit, clone); the reads are draft listing + contributor + enabled-features lookups.

## What it looks like (live, this run)

![17 listings abis](../seller/sec-17-listings-abis.png)
![18 listing drafts](../seller/sec-18-listing-drafts.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-17-listings-abis.png; seller/sec-18-listing-drafts.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /drafts/api/get | 2 | READ |
| ✅ | GET | sellercentral.amazon.in · /drafts/api/getContributors | 4 | READ |
| ✅ | GET | sellercentral.amazon.in · /lyp/api/enabledFeatures | 14 | READ |
| · | GET | sellercentral.amazon.in · /abis/index.html | — | READ |

## Response shapes (full field lists, from live capture)

- **`/drafts/api/get`** (2 fields): `draftListings`, `numberOfDrafts`
- **`/drafts/api/getContributors`** (4 fields): `contributorIds`, `isBlocked`, `marketplaceId`, `merchantAccountId`
- **`/lyp/api/enabledFeatures`** (14 fields): `asaEnabled`, `bulkEnabled`, `certifiedRefurbishedEnabled`, `connectApplicationEnabled`, `draftsEnabled`, `ebsEnabled`, `gtinExemptionEnabled`, `multiChannelConnectionEnabled`, `multiChannelSellingEnabled`, `offAmazonSelectionEnabled`, `offerTemplateEnabled`, `oneByOneEnabled`, `registrationOnlyEnabled`, `searchEnabled`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| ? | sellercentral.amazon.in · /abis/ajax/S3ImageUpload | WRITE | upload — G2 absolute prohibition |
| ? | sellercentral.amazon.in · /abis/ajax/clone-bsm-asin | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/clone-from-asin | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/clone-listing | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/create-listing | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/create-offer | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/create-pt-selection | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/create-variation-from-standalone | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/edit | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/edit-draft | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/edit-draft/save | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/write-offer | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/write-offer-full-form | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/ajax/write-variation-from-standalone | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/clone | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/clone-bsm-asin | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/clone-bsm-asin/ | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/clone-from-asin | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/clone-from-asin/ | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/clone/ | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/create | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/create-variation-from-standalone | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/create/ | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/createFromDraft | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/edit | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/edit-draft | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/listing/multi-create | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/product/ajax/CreationValidation | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/product/ajax/EditValidation | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /abis/product/ajax/OfferValidation | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /interactive/listing/workflow/create | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /interactive/listing/workflow/create/product_identity | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /interactive/listing/workflow/edit | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /interactive/listing/workflow/offer/offer | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /product/DisplayEditProduct | WRITE | write-verb constant/path token (G1: deny) |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /abis/ajax/EasyListConfig | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/brand/authorization | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/detailPageInfo | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/fix-listing | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/get-standalone-for-variation | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/losg-global/get-listing | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/offer-full-form | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/offer-prefilled | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/reconciledDetailsV2 | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/ajax/searchSkus | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/listing/offer-full-form | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/listing/syh | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/listing/v1/log | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/product/ajax/FeePreview.ajax | UNKNOWN |
| ? | sellercentral.amazon.in · /abis/product/ajax/MarketplaceListingEvent.ajax | UNKNOWN |
| GET | sellercentral.amazon.in · /m/products/edit | UNKNOWN |
| ? | sellercentral.amazon.in · /spsx/ajax/checkSellerQualification | UNKNOWN |
| ? | sellercentral.amazon.in · /spsx/ajax/getAttributesNormalizedValues | UNKNOWN |
| ? | sellercentral.amazon.in · /spsx/ajax/getContributionScope | UNKNOWN |
| ? | sellercentral.amazon.in · /spsx/ajax/getFBAEligibilityAndRecommendation | UNKNOWN |
| ? | sellercentral.amazon.in · /syh/DisplayCondition | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

