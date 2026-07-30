---
title: Listings-and-Catalog
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Listings-and-Catalog

> ⚠️ READ-ONLY. Catalogue: create/edit product, variants, listing search, image enrichment, alpha listings, documents.

**Endpoints in this section:** 207 — 23 read-safe (READ/READ_FILE), 89 write/export (out of scope), 95 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R-file | UNKNOWN | `seller.flipkart.com/napi/document/download` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/image-enricher/draft` | — | READ |
| R | GET | `seller.flipkart.com/napi/image-enricher/getServiceDetail` | — | READ |
| R | GET | `seller.flipkart.com/napi/image-enricher/rateCard` | — | READ |
| R | GET | `seller.flipkart.com/napi/image-enricher/serviceDiscovery` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/catalogFileDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/downloadErrorGroupingFile` | url | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/downloadNewGroupingTemplate` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/listing/frequently-used-vertical` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/getBrandSuggestions` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/getBulkVariantGroups` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/getVerticalGuidelines` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/inProgressBulkFeeds` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/instantGroupingStatus` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-insights-new` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-insights-reco-new` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-insights-reco-new-adoption` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-similar-listings` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/overallScore` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/overviewAPI` | — | READ |
| R | GET | `seller.flipkart.com/napi/listing/search-vertical` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/stockFileDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/stockFileDownloadRequestStatus` | — | READ_FILE |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/alphaListing/updateApprovalRequestStatus` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/checkAutofillVerticals` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/create` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/create-variants` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/delete-variants-data` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/draft` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-autofill-external-images-status` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-autoqc-guidelines` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-conditional-mandatory-attributes` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-product-title-preview` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-variants-data` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetchAutofillAttributes` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/get-fsn-attributes` | — | WRITE |
| GET | `seller.flipkart.com/napi/createProductV2/get-model-vertical-guidelines` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/getPartialDraft` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/predict-vertical` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/save-recommended-vertical` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/save-variants-data` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/submit` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/updatePartial` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/v1/create-variant` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/v1/delete-variants` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/v1/fetch-variant-definition` | — | WRITE |
| GET | `seller.flipkart.com/napi/createProductV2/verticalDefinition` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/createProductV2/verticalDefinitionV2` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/document/upload` | baseUrl | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/create-draft` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/delete-request` | deleteApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/fetchQCInProgressStatus` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/get-drafts` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/get-summary` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/is-fsn-owner` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/is-fsn-owner-bulk` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/save-draft` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/search` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/edit-product/submit-draft` | — | WRITE |
| GET | `seller.flipkart.com/napi/image-enricher/createDraft` | — | WRITE |
| GET | `seller.flipkart.com/napi/image-enricher/createPayment` | — | WRITE |
| GET | `seller.flipkart.com/napi/image-enricher/saveDraft` | — | WRITE |
| GET | `seller.flipkart.com/napi/image-enricher/submitDraft` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/addToGroup` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/bulk-edit-rate-limit` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/create-update-listings` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/deleteFeed` | — | WRITE |
| GET | `seller.flipkart.com/napi/listing/deleteRequest` | deleteApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/downloadReport` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/listing/enqueueDownload` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/listing/feed-listings-created/search` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/feed-vc-action` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/feed-vc-predict` | — | WRITE |
| GET | `seller.flipkart.com/napi/listing/image-uploader/images` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/request-download-images-catalog-file` | — | WRITE |
| GET | `seller.flipkart.com/napi/listing/image-uploader/requested-images-catalog-file-download-status` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/save-images` | — | WRITE |
| GET | `seller.flipkart.com/napi/listing/image-uploader/sku` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/instantCatalogUploadStatus` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-price-reco-update` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-return-reco-update` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/mspEnabled` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/priceUpdateHistory` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/removeFromGroup` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/report/generate-report` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/listing/return-reason-updated-time-duration` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/return-reco-update` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/saveVerticalPredictionsResponse` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/settlement-commissions` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/settlement-commissions-landing-forward-flow-zone` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/stockFileDownloadNUploadHistory` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/stockFileUploadRequestStatus` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/submit-size-chart` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/update-moq-fsp` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/update-size-chart` | updateWithPutApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/updateInventory` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/updateSellingPrice` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/uploadCatalogFileV2` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/uploadGroupingFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/uploadStockFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listing/video-context-create` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listingVideos/upload-video-chunk` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/listings-rest/fashion-trends-bulk-upload` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/delete-feed` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/download-history` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/request-error-file` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/request-file` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/requested-error-file-status` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/requested-file-status` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/search` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/upload-file` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/upload-status` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/alphaListing/getApprovalRequests` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/adopt-core-size-stock-reco` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/adopt-price-recommendations` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/adopt-stock-recommendations` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/commission-calc-mps` | fetchCommissionApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/conversion-insights` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/core-size-variant-for-a-groupid` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/entityDefinition` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fadetails` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fassured/details` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetch-deactivation-codes-count` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetch-default-location` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetch-recommendations-filter-count` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetch-seller-potential-sales-loss` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetchAllVariants` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetchAllVariantsData` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetchFsnGrade` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/fetchRecentBrands` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/filtered-inventory-info` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-complete-category-tree` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-deactivation-rating` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-info-by-id` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-suppresion-benchmark` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-tier` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-lqs-insight-recos` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-minoq-realized-impact` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-minoq-social-impact` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-misc-card-reviews` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-product-base-info` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-recommendations-impact` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-size-chart-categories` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-stock-reco-for-listing` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/get-stock-recommendations-impact` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/getCatalogErrorFileStatus` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/getHSNDetailsBasedOnVertical` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/getProductsList` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/getSellerMPAffinityFlag` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/getStockInsights` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/getTaxTags` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/getVariants` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/getVerticalPredictions` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/inProgressGroupingFeeds` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/inProgressSingle` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/inventoryStock` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/is-shopsy-seller` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/isSellerNew` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lag` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listing-performance-details` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listing-price-recommendation` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listings-price-recommendation` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listingsCountForStates` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listingsDataForStates` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listingsDataForStock` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listingsFilterValues` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listingsStateViewTemplate` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listingsStockCount` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/listingsStockRecoFilterValues` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-customers-liked` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-grade` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-grade-details` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-insights-new-bulk` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-insights-reco-new-adoption-bulk` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-insights-reco-new-bulk` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-metrics-impressions` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-ratings` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/lqs-returns` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/modifyFaSetting` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/modifyFaSettingSingleListing` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/modifyListingsSetting` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/moq-eligibility` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/oosTopListingsCount` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/pricing-reco-data` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/pricingInfo` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/quality-grade-percent` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/rate-card-identifier` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/recentCategoryTreeBulk` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/recentCategoryTreeSingle` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/report/check-report` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/requestCatalogErrorFile` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/return-insight-data` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/return-reason-filters` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/return-reason-percentage` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/return-reco-count-revenue` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/return-reco-count-revenue-listing-level` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/risk-recommendation-data` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/risk-recommendation-data-count` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/searchProduct` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/searchVertical` | treeAPI |
| UNKNOWN | `seller.flipkart.com/napi/listing/seller-quality-latch-on` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/sellerEligible` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/shopsy-budget/details` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/size-chart-definition` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/listing/stockRecoIngestionDate` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/top-verticals` | — |
| UNKNOWN | `seller.flipkart.com/napi/listing/voc-catalog-insight-adoption` | — |

## Live walk findings (VERIFIED 2026-07-30)

From the live Seller Hub Listings page (screenshots `sec-02`..`sec-05` in [[Flipkart-Live-Walk]]):
**Active 152 · Blocked 26 · Inactive 70 · Archived 182** (~430 FSNs total; only ~35% active,
278 not selling). Listing Quality score ~4.34; a "Listings at risk of losing visibility due to
catalog issues" banner + "one or more locations inactive". Tabs: All Listings / Add Listing;
states ACTIVE/INACTIVE/ARCHIVED + Listings-in-Progress each a distinct page.


## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
