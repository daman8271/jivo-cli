---
title: Coupons & Promotions
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, coupons-promotions]
status: studied
read_only: true
---

# Coupons & Promotions

**Portal:** Seller Central (3P) · **Section:** `seller/Coupons-Promotions` · **Endpoints catalogued:** 49 (29 read-safe, 28 PROVEN live · 5 out-of-scope · 15 unknown/telemetry)

Seller Coupons dashboard + Promotion Central. Reads: the promotions list (18 for JIVO Mart), merchant coupon rights, coupon config, ASIN/SKU search, fee preview, recommendations, tailoring, bulk-upload history. Every create/edit/cancel coupon path is WRITE.

## What it looks like (live, this run)

![14 coupons](../seller/sec-14-coupons.png)
![15 promotion central](../seller/sec-15-promotion-central.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-14-coupons.png; seller/sec-15-promotion-central.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /coupons/api/banners | — | READ |
| ✅ | GET | sellercentral.amazon.in · /coupons/api/config | 63 | READ |
| ✅ | GET | sellercentral.amazon.in · /coupons/api/getCouponPromotions | — | READ |
| ✅ | GET | sellercentral.amazon.in · /coupons/api/merchantInfo | 10 | READ |
| ✅ | GET | sellercentral.amazon.in · /coupons/api/tailoring | 29 | READ |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/ar-AE.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/de-DE.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-AU.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-CA.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-GB.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-IE.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-IN.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-SG.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-US.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/en-ZA.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/es-ES.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/es-MX.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/fr-BE.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/fr-FR.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/it-IT.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/ja-JP.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/nl-NL.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/pl-PL.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/pt-BR.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/sv-SE.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/th-TH.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/i18n/tr-TR.{hash}.i18next.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /coupons/undefined | — | READ |
| · | GET | sellercentral.amazon.in · /promotion-central/api/v1/settings | 6 | READ |

## Response shapes (full field lists, from live capture)

- **`/coupons/api/config`** (63 fields): `adModalImageLink`, `allowedCombinabilityTypes`, `allowedCouponTypes`, `amazonSiteLink`, `audiencesHelpLink`, `brandTailoringEnabled`, `budgetHelpPageLink`, `budgetOvershootHelpPageLink`, `budgetSetupInstructionLink`, `budgetSpentPercentForExpiringSoon`, `budgetType`, `bulkUploadHelpUrl`, `campaignManagerLink`, `clipFee`, `couponRecommendationsEnabled`, `couponTipsLink`, `currency`, `currencyName`, `dashboardHelpLink`, `dashboardHelpLinkBeta`, `daysBeforeEndDateForExpiringSoon`, `defaultLanguageCode`, `discountTypesSupported`, `discountedRedemptionFee`, `editBeforeStartDateInDaysV2`, `editHelpLink`, `fidoFeesSupported`, `fulfillmentPrograms`, `legacyBudgetType`, `legacyDiscountTypesSupported`, `localeTitleRegex`, `marketplaceId`, `maxAsins`, `maxBudget`, `maxCouponDuration`, `maxCouponDurationByCouponType`, `maxCouponDurationByCouponType.personalized`, `maxCouponDurationByCouponType.reorder_rewards`, `maxCouponDurationByCouponType.standard`, `maxCouponDurationByCouponType.subscribe_and_save` …
- **`/coupons/api/merchantInfo`** (10 fields): `amazonAccelerator`, `amazonLaunchpad`, `canCreateAndEditCoupons`, `canCreatePersonalizedCoupons`, `isMarketplaceSupported`, `isMerchantDenylisted`, `marketplaceId`, `merchantAccountId`, `merchantSubscriptionType`, `rights`
- **`/coupons/api/tailoring`** (29 fields): `groupToAudiences`, `groupToAudiences.Brand`, `groupToAudiences.Brand.description`, `groupToAudiences.Brand.id`, `groupToAudiences.Brand.name`, `groupToAudiences.Brand.type`, `groupToAudiences.Custom`, `groupToAudiences.Custom.description`, `groupToAudiences.Custom.id`, `groupToAudiences.Custom.name`, `groupToAudiences.Custom.type`, `groupToAudiences.Program`, `groupToAudiences.Program.description`, `groupToAudiences.Program.id`, `groupToAudiences.Program.name`, `groupToAudiences.Program.type`, `groupToAudiences.Reorder`, `groupToAudiences.Reorder.description`, `groupToAudiences.Reorder.id`, `groupToAudiences.Reorder.name`, `groupToAudiences.Reorder.type`, `groupToSubGroups`, `groupToSubGroups.Brand`, `groupToSubGroups.Brand.options`, `groupToSubGroups.Brand.tooltip`, `groups`, `groups.id`, `groups.name`, `groups.supportedCouponTypes`
- **`/promotion-central/api/v1/settings`** (6 fields): `error`, `error.code`, `error.name`, `error.reason`, `error.retryable`, `message`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| ? | sellercentral.amazon.in · /coupons/api/cancelCouponPromotion | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /coupons/api/editCouponPromotion | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /coupons/api/reportPromotionApprovalDecision | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /coupons/api/v2/bulkUploadHistory | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /coupons/api/v2/uploadBulkFile | WRITE | upload — G2 absolute prohibition |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /coupons-dashboard-page | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/asin | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/couponPromotion | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/couponPromotion/products | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/feePreview | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/product-selection/sns/ | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/recommendations | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/search | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/sku | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/tailoring/merchant | UNKNOWN |
| ? | sellercentral.amazon.in · /coupons/api/v2/bulkItem | UNKNOWN |
| GET | sellercentral.amazon.in · /coupons/api/weblabs/all | NOISE |
| ? | sellercentral.amazon.in · /coupons/logs | NOISE |
| ? | sellercentral.amazon.in · /promotion-central | UNKNOWN |
| ? | sellercentral.amazon.in · /promotion/psp/ | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

