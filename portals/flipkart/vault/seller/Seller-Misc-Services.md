---
title: Seller-Misc-Services
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Seller-Misc-Services

> ⚠️ READ-ONLY. Assorted seller napi micro-services not owned by another section (telemetry, home widgets, OTP, tracking).

**Endpoints in this section:** 62 — 7 read-safe (READ/READ_FILE), 16 write/export (out of scope), 39 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/get-locations` | — | READ |
| R | GET | `seller.flipkart.com/napi/getSellerStoriesDetails` | — | READ |
| R | GET | `seller.flipkart.com/napi/metrics/darwin/v3/tiering-metrics` | — | READ |
| R | GET | `seller.flipkart.com/napi/metrics/homePage/goalsDetails` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/metrics/priceRecoErrorFileDownload` | PRICE_RECO_ERROR_FILE_DOWNLOAD_API | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/metrics/sbpPriceRecoErrorFileDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/smart-inwarding/downloadQCFile` | — | READ_FILE |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/cancelled_orders/fetchV2` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/getHomePageUpdates` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/lbhw/updateV2` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics-rest/competitor-products/bulk-upload` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/updateQuetionnaireResponse` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/priceRecommendationUpdate` | priceRecommendationUpdateRequestURL | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/create-rule` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/delete-rule` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/update-rule` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/updateOosInsightData` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/priceRecoFileUploadRequestStatus` | PRICE_RECO_FILE_UPLOAD_STATUS | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/sbpPriceRecoFileUploadStatus` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/uploadDocumentImage` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/uploadPriceRecoFile` | PRICE_RECO_FILE_UPLOAD_API | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/uploadPriceRecoSbpFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/scf/uploadImage` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| POST | `seller.flipkart.com/api/send-otp` | — |
| POST | `seller.flipkart.com/api/validate-otp` | — |
| UNKNOWN | `seller.flipkart.com/napi/` | — |
| UNKNOWN | `seller.flipkart.com/napi/contextualFaq/getFaqs` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/darwin/finalTier` | fetchDarwinApi |
| UNKNOWN | `seller.flipkart.com/napi/fdp/batch-events` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/get-marketing-card` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/getCallBackDetails` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/getRtbbdDetails` | getRtbbdData |
| UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/getQuestionnaire` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/metrics-data` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/tiering-metrics` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/get-filters` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/generalRecoCall` | lastUpdatedTime |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/getImpact` | impactURL |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/getImpactCsv` | downloadCsv |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/getRUReccomendationCards` | zoneApi |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/insightRecommendation` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/oosInsight` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/oosInsightData` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/count` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/data` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/filters` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/data` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/history` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/recommendationData` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/productDetailsView` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/rsppNotification` | — |
| POST | `seller.flipkart.com/napi/metrics/search` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/search/min_max_dates` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/dropShipBreaches` | dropShipBreaches |
| UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/packageAdherence` | packageAdherence |
| UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/recommendations` | zoneApi |
| UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/zoneDetailForRU` | — |
| UNKNOWN | `seller.flipkart.com/napi/requestForCallBack` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/seller-capability/fetch-capability` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/shipping/getShippingFee` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/tracking/trackReturns` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/voice/translate` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
