---
title: Growth-Insights-and-Assistance
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, platform, read-only]
status: studied
---

# Growth-Insights-and-Assistance

> ⚠️ READ-ONLY. SIR insights, guided assistance, gamification, GA content, home-page growth widgets.

**Endpoints in this section:** 66 — 0 read-safe (READ/READ_FILE), 22 write/export (out of scope), 44 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/update-usage` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/createBookmark` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/createIncident_v2` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/createInstanceHelpSection` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/createInstance_v2` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/deleteBookmark` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/deleteInstance` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/getBookmarks` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/getBulkUploadStatus` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/submitSurvey` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ga/uploadAttachment` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/riddler/bookmarkQuestion` | — | WRITE |
| GET | `seller.flipkart.com/napi/riddler/fetchAssignedFsnsForSeller` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/riddler/fetchAssignedQuestionsCount` | fetchApi | WRITE |
| GET | `seller.flipkart.com/napi/riddler/fetchAssignedQuestionsForProduct` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/bookmark-product-opportunity` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/bookmarks-product-opportunities-v2` | — | WRITE |
| GET | `seller.flipkart.com/napi/seller-insightsV2/downloadReport/` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/report/generateReport` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/unbookmark-product-opportunity` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/update-seller-intent-msku-opportunities` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/update-seller-profile` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/learning-pilot-faqs` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/sample-attachment` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/search-faqs` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/top-faqs` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ga/diagnosis` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ga/gaFeedback` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/gaSearch_v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/get-config-service-data` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/get-questionnaires` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ga/getAssistanceCategories` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ga/getIssuesForFilter` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/getNodeId` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/getNodeId_v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/getSubIssuesForFilter` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/getVideos` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/issue-types` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/selectInstanceNodeHelpSection` | — |
| UNKNOWN | `seller.flipkart.com/napi/ga/selectInstanceNode_v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/yoda/actionHistory` | yodaActionHistory |
| UNKNOWN | `seller.flipkart.com/napi/metrics/yoda/sellerIncentive` | sellerIncentive |
| UNKNOWN | `seller.flipkart.com/napi/riddler/markQuestionAsNotInterested` | — |
| UNKNOWN | `seller.flipkart.com/napi/riddler/notifyAnswerEvent` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/bestseller-product-opportunities-v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/dismiss-product-opportunity` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/get-approval-status` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/get-seller-profile` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/msku-attribute-listings-view` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/msku-recommendations` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/oos-product-opportunities-v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/product-opportunities-filter-values` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/product-opportunities-impact` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/product-opportunities-v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/report/checkReports` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/shopsy-product-opportunities-v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/supervalue-product-opportunities-v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/trending-product-opportunities-v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/trending_design_recommendations_v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/value-engg-opportunities-v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/welcome/data` | getViewData |
| UNKNOWN | `seller.flipkart.com/napi/welcome/get-commission` | getCommission |
| UNKNOWN | `seller.flipkart.com/napi/welcome/get-complete-category-tree` | getAllCategories |
| UNKNOWN | `seller.flipkart.com/napi/welcome/get-config-service-data` | getConfigServiceData |
| UNKNOWN | `seller.flipkart.com/napi/welcome/get-top-sellers-data` | fetchTopSellers |
| UNKNOWN | `seller.flipkart.com/napi/welcome/send-feedback` | sendFeedbackData |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
