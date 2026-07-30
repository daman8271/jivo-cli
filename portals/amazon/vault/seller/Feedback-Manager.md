---
title: Feedback Manager
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, feedback-manager]
status: studied
read_only: true
---

# Feedback Manager

**Portal:** Seller Central (3P) · **Section:** `seller/Feedback-Manager` · **Endpoints catalogued:** 8 (8 read-safe, 8 PROVEN live · 0 out-of-scope · 0 unknown/telemetry)

Seller feedback (star ratings from buyers) — aggregates over 30D/90D/365D/LIFETIME, per-rating breakdown, order-performance bar, and the feedback list. Fully live-proven GET reads: JIVO Mart lifetime 3.8★ across 73 reviews.

## What it looks like (live, this run)

![22 feedback manager](../seller/sec-22-feedback-manager.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-22-feedback-manager.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /fbmapi/v1/aggregates | 123 | READ |
| ✅ | GET | sellercentral.amazon.in · /fbmapi/v1/csrf | — | READ |
| ✅ | GET | sellercentral.amazon.in · /fbmapi/v1/feedbacks | — | READ |
| ✅ | GET | sellercentral.amazon.in · /fbmapi/v1/metadata | 21 | READ |
| ✅ | GET | sellercentral.amazon.in · /fbmapi/v1/orderperformanceSellerBar | 4 | READ |
| ✅ | GET | sellercentral.amazon.in · /fbmapi/v1/orderperformanceUIVersions | 3 | READ |
| ✅ | GET | sellercentral.amazon.in · /feedback-manager/i18n/en-IN.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /feedback-manager/i18n/en-US.json | — | READ_FILE |

## Response shapes (full field lists, from live capture)

- **`/fbmapi/v1/aggregates`** (123 fields): `durationResponseMap`, `durationResponseMap.30D`, `durationResponseMap.30D.durationName`, `durationResponseMap.30D.effectiveRating`, `durationResponseMap.30D.meanRating`, `durationResponseMap.30D.negativeCount`, `durationResponseMap.30D.negativeWithText`, `durationResponseMap.30D.neutralCount`, `durationResponseMap.30D.neutralWithText`, `durationResponseMap.30D.positiveCount`, `durationResponseMap.30D.positiveWithText`, `durationResponseMap.30D.rating1`, `durationResponseMap.30D.rating1Percentage`, `durationResponseMap.30D.rating1PercentageDisplayString`, `durationResponseMap.30D.rating1WithText`, `durationResponseMap.30D.rating2`, `durationResponseMap.30D.rating2Percentage`, `durationResponseMap.30D.rating2PercentageDisplayString`, `durationResponseMap.30D.rating2WithText`, `durationResponseMap.30D.rating3`, `durationResponseMap.30D.rating3Percentage`, `durationResponseMap.30D.rating3PercentageDisplayString`, `durationResponseMap.30D.rating3WithText`, `durationResponseMap.30D.rating4`, `durationResponseMap.30D.rating4Percentage`, `durationResponseMap.30D.rating4PercentageDisplayString`, `durationResponseMap.30D.rating4WithText`, `durationResponseMap.30D.rating5`, `durationResponseMap.30D.rating5Percentage`, `durationResponseMap.30D.rating5PercentageDisplayString`, `durationResponseMap.30D.rating5WithText`, `durationResponseMap.365D`, `durationResponseMap.365D.durationName`, `durationResponseMap.365D.effectiveRating`, `durationResponseMap.365D.meanRating`, `durationResponseMap.365D.negativeCount`, `durationResponseMap.365D.negativeWithText`, `durationResponseMap.365D.neutralCount`, `durationResponseMap.365D.neutralWithText`, `durationResponseMap.365D.positiveCount` …
- **`/fbmapi/v1/metadata`** (21 fields): `defaultTimeZoneName`, `languageOfPreference`, `marketplaceId`, `merchantId`, `primaryDomainName`, `rightsPeekNow`, `treatments`, `treatments.CSQ_CLICKSTREAM_TRACKING_1277566`, `treatments.CSQ_V32_BANNER_WW_1409833`, `treatments.FBMWEBSITE_ANNOUNCEMENT_CSMETRICS_1082697`, `treatments.FBM_CSQ_907711`, `treatments.FBM_PAGINATION_NAV_ONLY_1386454`, `treatments.FBM_TTR_P1_1226026`, `treatments.FEEDBACK_REMOVAL_CONFIRMATION_MESSAGE_UPDATE_1363179`, `treatments.FEEDBACK_REMOVAL_STRIKETHROUGH_CRITERIA_1291967`, `treatments.RDS_647298`, `treatments.SPG_CSQ_WORLDWIDE_1111801`, `treatments.SPG_FBM_APPEALS_PANEL_REASON_CODES_1382492`, `treatments.SPG_FBM_APPEAL_TRACKING_P3_1406061`, `treatments.SP_SERVICES_FBM_APPEAL_TRACKING_P3_SXBR_1417283`, `treatments.SP_SERVICES_FBM_HISTOGRAM_RATING_1405821`
- **`/fbmapi/v1/orderperformanceSellerBar`** (4 fields): `metricsResponseMap`, `metricsResponseMap.CSQR_CPU`, `metricsResponseMap.CSQR_EDR`, `metricsResponseMap.CSQR_SLA`
- **`/fbmapi/v1/orderperformanceUIVersions`** (3 fields): `averageSellerPerformance`, `topPerformingSellerBar`, `yourPerformance`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

_None catalogued in this section._

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

