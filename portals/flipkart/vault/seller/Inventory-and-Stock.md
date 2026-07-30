---
title: Inventory-and-Stock
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Inventory-and-Stock

> ⚠️ READ-ONLY. Unified inventory, inventory health, SFX stock updates, SRM.

**Endpoints in this section:** 60 — 17 read-safe (READ/READ_FILE), 19 write/export (out of scope), 24 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/consignment/handleDownloadSplitsCSV` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/download/fsn/label` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/BulkRecallFileDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/bulk/download` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/downloadErrorSKUFile` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/sfx/UIVFilterValues` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/downloadRecoReport` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/downloadStatusUIVReport` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/downloadUIVReport` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/sfx/fetchDispatchAddress` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/consignment/download` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recall/download` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/sfx/seller/warehouseDetails` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/streamDownloadedUIVReport` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/srm/GSTIN` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/srm/getRecallPreference` | — | READ |
| R | GET | `seller.flipkart.com/napi/srm/managerDetails` | — | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/BulkRecallFileUpload` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/address/add` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/bulkStockUpdateProcessStatus` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/bulkStockUpdateProcessStatusV2` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/processBulkStockUpdateFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/processBulkStockUpdateFileV2` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/reports/generateReport` | updateApi | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/sfx/reports/getGeneratedReports` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recall/confirm` | updateApi | WRITE |
| GET | `seller.flipkart.com/napi/sfx/seller/bulk/recall/delete` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/streamBulkStockUpdateFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/triggerStockUpdateDownload` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/updateListingsInventory` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/updateListingsInventoryViaSigs` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/uploadBulkConsignment` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sfx/uploadRecallFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/srm/submitQuestionnaireV3` | submitQuestionnaire | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/srm/submitSkippedQuestionnaireV3` | submitSkippedQuestionnaire | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/srm/updateClosedQuestionnaire` | updateClosedQuestionnaire | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/inventory-rest/` | — |
| UNKNOWN | `seller.flipkart.com/napi/sfx/getAllStates` | — |
| UNKNOWN | `seller.flipkart.com/napi/sfx/getFbfGstinDocumentDetails` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/getUIVListDetails` | — |
| UNKNOWN | `seller.flipkart.com/napi/sfx/getUIVRecoListDetails` | — |
| UNKNOWN | `seller.flipkart.com/napi/sfx/recall/getRecallReturnDetails` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/recall/sellable` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/recall/sellable/details` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/recall/unsellable` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/recall/unsellable/details` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/reports/getReportGroup/details` | fetchApiUrl |
| UNKNOWN | `seller.flipkart.com/napi/sfx/reports/getReportGroups` | fetchBizReportsApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recalls` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recalls/jobstatus` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sfx/seller/recall/details` | — |
| UNKNOWN | `seller.flipkart.com/napi/sfx/seller/recall/details/v2` | — |
| UNKNOWN | `seller.flipkart.com/napi/sfx/seller/recalls` | — |
| UNKNOWN | `seller.flipkart.com/napi/sfx/validateFbfGstin` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/srm/changeRecallPreference` | — |
| UNKNOWN | `seller.flipkart.com/napi/srm/getFacilityList` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/srm/getQuestionnaireByFeature` | getQuestionnaireByFeatureName |
| UNKNOWN | `seller.flipkart.com/napi/srm/getQuestionnaireData` | getQuestionnaireData |
| UNKNOWN | `seller.flipkart.com/napi/srm/locationNames` | — |
| UNKNOWN | `seller.flipkart.com/napi/srm/preLoginIncident` | contactSS |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
