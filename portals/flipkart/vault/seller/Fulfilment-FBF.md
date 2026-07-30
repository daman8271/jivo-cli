---
title: Fulfilment-FBF
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Fulfilment-FBF

> ⚠️ READ-ONLY. Fulfilled-By-Flipkart (FBF/FAssured) & FBF-Lite inbound, stock and shipment handling.

**Endpoints in this section:** 79 — 23 read-safe (READ/READ_FILE), 23 write/export (out of scope), 33 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadActionTemplate` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadAutoEInvoice` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadCostDetailsErrorFile` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadCostDetailsTemplate` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadRecallV2Report` | — | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/fbf/recall/getDocumentStatus` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/fbf/recall/getInvoiceCostDetailsStatus` | — | READ |
| R | GET | `seller.flipkart.com/napi/fbf/recall/search` | — | READ |
| R | GET | `seller.flipkart.com/napi/fbf/recall/validateSKU` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfLite/downloadBinTemplate` | AVAILABLE_BINS | READ_FILE |
| R | GET | `seller.flipkart.com/napi/fbfLite/get/enrich` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/get/shipment/pick/list` | updateApi | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/getRecallDetails` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/inventory` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/pick_list/shipment/pack` | updateApi | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfLite/print/invoice` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/fbfLite/recalls` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/sidelinePicklistGroup` | updateApi | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/downloadDocument` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/downloadGstinDocument` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/fbfOnboarding/getAddressList` | — | READ |
| R | GET | `seller.flipkart.com/napi/fbfOnboarding/getEInvoiceOnboardingDetails` | — | READ |
| R | GET | `seller.flipkart.com/napi/fbfOnboarding/getReturnAddressList` | — | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/bulk-approve` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/bulk-reject` | — | WRITE |
| GET | `seller.flipkart.com/napi/fbf/recall/delete` | updateApi | WRITE |
| PUT | `seller.flipkart.com/napi/fbf/recall/submitRecallDocs` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbf/recall/updateInvoiceCostDetails` | — | WRITE |
| PUT | `seller.flipkart.com/napi/fbf/recall/updateMetaAddress` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadAutoEInvoice` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadEInvoice` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadEInvoiceDoc` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadInvoiceCostDetails` | — | WRITE |
| GET | `seller.flipkart.com/napi/fbf/recall/uploadSKUErrorFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/create/pick_list` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/deleteGroupListing` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/downloadGroupListingEditFile` | — | WRITE |
| GET | `seller.flipkart.com/napi/fbfLite/shipments/is_confirm` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/uploadRecallFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/fbfgstinDocumentUpload` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/generateRentalAgreement` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/saveAsDraft` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/saveTermsSelection` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/uploadDocument` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/uploadVeritas` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fbflite/generatePicklist` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/filters` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/search` | r_e |
| UNKNOWN | `seller.flipkart.com/napi/fbf/recall/filter` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbf/recall/getStateCount` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbf/warehouseDetails` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/audit/answers` | submitAnswers |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/audit/latest` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/audit/questions` | getQeastions |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/closePicklist` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/fetchCloseablePicklist` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/forceClosePicklist` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/get/pending/pick_list` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/get/pick_list` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/getGroupListingTemplate` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/getInventoryAgeingReport` | AGEING_REPORT |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/getListingDetails` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/inwardProducts` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/mark/pick_progress` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/markLostPicklistGroup` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/moveInventory` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/pick_list/preference` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/pick_list/shipment/rts` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/picklist/allTypeCounts` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/print/prn` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/recallItems` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfLite/validateIMEI` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/allocateCA` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/getCurrentState` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/getRequiredDocuments` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/markLocationAsVerified` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/storeNicCredentials` | — |
| UNKNOWN | `seller.flipkart.com/napi/fbflite/getOrderHistory` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fbflite/printPickList` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
