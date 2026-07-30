---
title: Flipkart Endpoints (read-only master index)
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, endpoints, master-index, read-only]
---

# Flipkart — Read-Only Master Endpoint Inventory

Every distinct API path found across the Seller Hub + Vendor Hub JS corpus (`captures/js/*`), classified. **968 distinct endpoints.** `READ`/`READ_FILE` rows are safe to expose in a read-only CLI; `WRITE`/`EXPORT` mutate or side-effect and are held out of scope; `UNKNOWN` rows have a binding but the method/posture is unresolved from the minified source — per **G1 they are denied by default** (documented, never wired).

Atlas: [[00-Flipkart-Atlas]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Data inventory: [[Flipkart-Data-Inventory]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]]

## Roll-up

| Class | Count | Exposed in CLI? |
|---|---|---|
| READ (JSON) | 137 | yes |
| READ_FILE (download existing) | 79 | yes (download-only) |
| WRITE | 304 | **never** |
| EXPORT (enqueue/generate) | 26 | **never** (G2) |
| UNKNOWN / UNKNOWN_READLIKE | 422 | **never** (G1 denied) |
| **TOTAL** | **968** | |

Legend: `READ` pure JSON query · `READ_FILE` downloads an already-generated binary · `WRITE` mutates data/state · `EXPORT` creates a report-request row (a WRITE per G2) · `UNKNOWN`/`?` method or read-vs-write not proven from the bundle → to-confirm, never exposed blind · `?read` = read-like verb but POST/unknown.

# SELLER lane

## [[Communications-and-Cases]]

Seller-buyer communications (SBC), case manager, notifications.  
**40 endpoints** — 3 read-safe · 13 write/export · 24 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/get-notifications` | READ |
| R | GET | `seller.flipkart.com/napi/get-notifications-count` | READ |
| R | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getChatKey` | READ |
| ? | UNKNOWN | `seller.flipkart.com/napi/case-manager/general-tickets` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/case-manager/issue-schema` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/case-manager/issue-seller-close` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/case-manager/issue-thread` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/case-manager/sub-issue-types` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/notifications/action` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/chatMeta` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/existingBuyer` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/postChatMessages` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/sellerHeartBeat` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/case-manager/getSellerDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/case-manager/issues-search` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getActorState` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getBuyerList` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getChatMessageCount` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getChatMessages` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getConversationList` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getEvents` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getLatestEvents` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getListingForSeller` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getMetricsData` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getPageBuyerList` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/searchReturnId` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/sirCounts` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/case-manager/getCreateTicketForm` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/case-manager/spf-claims` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/case-manager/submitIssue` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/case-manager/submitReply` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/mark-all-notifications` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/notifications/update` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/createConversation` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/createSirIncidents` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/isSellerEnabled` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/proposeCancellation` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/updateActor` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/updateActorState` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/updateConversation` | WRITE |

## [[Compliance-and-Regulation]]

Regulation approvals, audit, approval-store, product compliance.  
**15 endpoints** — 10 read-safe · 1 write/export · 4 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/approval-store/latest-status` | READ |
| R | GET | `seller.flipkart.com/napi/approval-store/questions` | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditDetails` | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditMetaData` | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditPQDetails` | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditPQResults` | READ |
| R | GET | `seller.flipkart.com/napi/audit/categoriesFilter` | READ |
| R | GET | `seller.flipkart.com/napi/regulation/approvalRequest` | READ |
| R | GET | `seller.flipkart.com/napi/regulation/approvalStatusWithProcessId` | READ |
| R | GET | `seller.flipkart.com/napi/regulation/auditDetails` | READ |
| ? | UNKNOWN | `seller.flipkart.com/napi/approval-store/requestsV2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/audit/audits` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/approval-store/requestsV2-count` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/regulation/approvalStatus` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/audit/updateAudit` | WRITE |

## [[Fulfilment-FBF]]

Fulfilled-By-Flipkart (FBF/FAssured) & FBF-Lite inbound, stock and shipment handling.  
**79 endpoints** — 23 read-safe · 23 write/export · 33 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/fbf/recall/getInvoiceCostDetailsStatus` | READ |
| R | GET | `seller.flipkart.com/napi/fbf/recall/search` | READ |
| R | GET | `seller.flipkart.com/napi/fbf/recall/validateSKU` | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/get/enrich` | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/get/shipment/pick/list` | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/getRecallDetails` | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/inventory` | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/pick_list/shipment/pack` | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/recalls` | READ |
| R | GET | `seller.flipkart.com/napi/fbfLite/sidelinePicklistGroup` | READ |
| R | GET | `seller.flipkart.com/napi/fbfOnboarding/getAddressList` | READ |
| R | GET | `seller.flipkart.com/napi/fbfOnboarding/getEInvoiceOnboardingDetails` | READ |
| R | GET | `seller.flipkart.com/napi/fbfOnboarding/getReturnAddressList` | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadActionTemplate` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadAutoEInvoice` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadCostDetailsErrorFile` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadCostDetailsTemplate` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/downloadRecallV2Report` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/fbf/recall/getDocumentStatus` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfLite/downloadBinTemplate` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfLite/print/invoice` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/downloadDocument` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/downloadGstinDocument` | READ_FILE |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/audit/answers` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/audit/latest` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/audit/questions` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/inwardProducts` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/mark/pick_progress` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/moveInventory` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/print/prn` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/recallItems` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfLite/validateIMEI` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/allocateCA` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/markLocationAsVerified` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/storeNicCredentials` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/filters` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/search` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/filter` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/getStateCount` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbf/warehouseDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/closePicklist` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/fetchCloseablePicklist` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/forceClosePicklist` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/get/pending/pick_list` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/get/pick_list` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/getGroupListingTemplate` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/getInventoryAgeingReport` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/getListingDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/markLostPicklistGroup` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/pick_list/preference` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/pick_list/shipment/rts` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfLite/picklist/allTypeCounts` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/getCurrentState` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/getRequiredDocuments` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbflite/getOrderHistory` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fbflite/printPickList` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/bulk-approve` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbf/mdf/seller-requirements/bulk-reject` | WRITE |
| W | GET | `seller.flipkart.com/napi/fbf/recall/delete` | WRITE |
| W | PUT | `seller.flipkart.com/napi/fbf/recall/submitRecallDocs` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/updateInvoiceCostDetails` | WRITE |
| W | PUT | `seller.flipkart.com/napi/fbf/recall/updateMetaAddress` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadAutoEInvoice` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadEInvoice` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadEInvoiceDoc` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbf/recall/uploadInvoiceCostDetails` | WRITE |
| W | GET | `seller.flipkart.com/napi/fbf/recall/uploadSKUErrorFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfLite/create/pick_list` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfLite/deleteGroupListing` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfLite/downloadGroupListingEditFile` | WRITE |
| W | GET | `seller.flipkart.com/napi/fbfLite/shipments/is_confirm` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfLite/uploadRecallFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/fbfgstinDocumentUpload` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/generateRentalAgreement` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/saveAsDraft` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/saveTermsSelection` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/uploadDocument` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbfOnboarding/uploadVeritas` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fbflite/generatePicklist` | WRITE |

## [[Inventory-and-Stock]]

Unified inventory, inventory health, SFX stock updates, SRM.  
**60 endpoints** — 17 read-safe · 19 write/export · 24 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| W-export | UNKNOWN | `seller.flipkart.com/napi/sfx/reports/generateReport` | EXPORT |
| R | GET | `seller.flipkart.com/napi/sfx/UIVFilterValues` | READ |
| R | GET | `seller.flipkart.com/napi/sfx/fetchDispatchAddress` | READ |
| R | GET | `seller.flipkart.com/napi/sfx/seller/warehouseDetails` | READ |
| R | GET | `seller.flipkart.com/napi/srm/GSTIN` | READ |
| R | GET | `seller.flipkart.com/napi/srm/getRecallPreference` | READ |
| R | GET | `seller.flipkart.com/napi/srm/managerDetails` | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/consignment/handleDownloadSplitsCSV` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/download/fsn/label` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/BulkRecallFileDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/bulk/download` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/downloadErrorSKUFile` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/downloadRecoReport` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/downloadStatusUIVReport` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/downloadUIVReport` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/consignment/download` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recall/download` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/sfx/streamDownloadedUIVReport` | READ_FILE |
| ? | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sfx/recall/sellable` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sfx/recall/unsellable` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recalls` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/recalls` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/sfx/validateFbfGstin` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/srm/changeRecallPreference` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/srm/locationNames` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/srm/preLoginIncident` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/getAllStates` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/getFbfGstinDocumentDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/getUIVListDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/getUIVRecoListDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/recall/getRecallReturnDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/recall/sellable/details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/recall/unsellable/details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/reports/getReportGroup/details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/reports/getReportGroups` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recalls/jobstatus` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/recall/details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/recall/details/v2` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/srm/getFacilityList` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/srm/getQuestionnaireByFeature` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/srm/getQuestionnaireData` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/inventory-rest/recall/BulkRecallFileUpload` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/address/add` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/bulkStockUpdateProcessStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/bulkStockUpdateProcessStatusV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/processBulkStockUpdateFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/processBulkStockUpdateFileV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/reports/getGeneratedReports` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/seller/bulk/recall/confirm` | WRITE |
| W | GET | `seller.flipkart.com/napi/sfx/seller/bulk/recall/delete` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/streamBulkStockUpdateFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/triggerStockUpdateDownload` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/updateListingsInventory` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/updateListingsInventoryViaSigs` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/uploadBulkConsignment` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sfx/uploadRecallFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/srm/submitQuestionnaireV3` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/srm/submitSkippedQuestionnaireV3` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/srm/updateClosedQuestionnaire` | WRITE |

## [[Lending-and-Growth-Capital]]

Seller lending and Flipkart Growth Capital applications.  
**6 endpoints** — 0 read-safe · 3 write/export · 3 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| ? | UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/describe-offer` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/es-discovery` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/getOffers` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/acceptApplication` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/create-lead` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/declineApplication` | WRITE |

## [[Listings-and-Catalog]]

Catalogue: create/edit product, variants, listing search, image enrichment, alpha listings, documents.  
**207 endpoints** — 23 read-safe · 89 write/export · 95 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| W-export | UNKNOWN | `seller.flipkart.com/napi/listing/downloadReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/listing/enqueueDownload` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/listing/report/generate-report` | EXPORT |
| R | GET | `seller.flipkart.com/napi/image-enricher/draft` | READ |
| R | GET | `seller.flipkart.com/napi/image-enricher/getServiceDetail` | READ |
| R | GET | `seller.flipkart.com/napi/image-enricher/rateCard` | READ |
| R | GET | `seller.flipkart.com/napi/image-enricher/serviceDiscovery` | READ |
| R | GET | `seller.flipkart.com/napi/listing/frequently-used-vertical` | READ |
| R | GET | `seller.flipkart.com/napi/listing/getBrandSuggestions` | READ |
| R | GET | `seller.flipkart.com/napi/listing/getBulkVariantGroups` | READ |
| R | GET | `seller.flipkart.com/napi/listing/getVerticalGuidelines` | READ |
| R | GET | `seller.flipkart.com/napi/listing/inProgressBulkFeeds` | READ |
| R | GET | `seller.flipkart.com/napi/listing/instantGroupingStatus` | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-insights-new` | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-insights-reco-new` | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-insights-reco-new-adoption` | READ |
| R | GET | `seller.flipkart.com/napi/listing/lqs-similar-listings` | READ |
| R | GET | `seller.flipkart.com/napi/listing/overallScore` | READ |
| R | GET | `seller.flipkart.com/napi/listing/overviewAPI` | READ |
| R | GET | `seller.flipkart.com/napi/listing/search-vertical` | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/document/download` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/catalogFileDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/downloadErrorGroupingFile` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/downloadNewGroupingTemplate` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/stockFileDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/listing/stockFileDownloadRequestStatus` | READ_FILE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/alphaListing/getApprovalRequests` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/adopt-core-size-stock-reco` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/adopt-price-recommendations` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/adopt-stock-recommendations` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/commission-calc-mps` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/conversion-insights` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/core-size-variant-for-a-groupid` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/entityDefinition` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fadetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fassured/details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetch-deactivation-codes-count` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetch-default-location` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetch-recommendations-filter-count` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetch-seller-potential-sales-loss` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetchAllVariants` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetchAllVariantsData` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetchFsnGrade` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/fetchRecentBrands` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/filtered-inventory-info` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-complete-category-tree` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-deactivation-rating` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-info-by-id` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-suppresion-benchmark` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-listings-tier` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-lqs-insight-recos` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-minoq-realized-impact` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-minoq-social-impact` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-misc-card-reviews` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-product-base-info` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-recommendations-impact` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-size-chart-categories` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-stock-reco-for-listing` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/get-stock-recommendations-impact` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getCatalogErrorFileStatus` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getHSNDetailsBasedOnVertical` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getProductsList` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getSellerMPAffinityFlag` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getStockInsights` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getTaxTags` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getVariants` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/getVerticalPredictions` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/inProgressGroupingFeeds` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/inProgressSingle` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/inventoryStock` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/is-shopsy-seller` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/isSellerNew` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lag` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listing-performance-details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listing-price-recommendation` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listings-price-recommendation` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listingsCountForStates` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listingsDataForStates` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listingsDataForStock` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listingsFilterValues` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listingsStateViewTemplate` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listingsStockCount` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/listingsStockRecoFilterValues` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-customers-liked` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-grade` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-grade-details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-insights-new-bulk` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-insights-reco-new-adoption-bulk` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-insights-reco-new-bulk` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-metrics-impressions` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-ratings` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-returns` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/modifyFaSetting` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/modifyFaSettingSingleListing` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/modifyListingsSetting` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/moq-eligibility` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/oosTopListingsCount` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/pricing-reco-data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/pricingInfo` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/quality-grade-percent` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/rate-card-identifier` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/recentCategoryTreeBulk` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/recentCategoryTreeSingle` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/report/check-report` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/requestCatalogErrorFile` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/return-insight-data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/return-reason-filters` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/return-reason-percentage` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/return-reco-count-revenue` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/return-reco-count-revenue-listing-level` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/risk-recommendation-data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/risk-recommendation-data-count` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/searchProduct` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/searchVertical` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/seller-quality-latch-on` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/sellerEligible` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/shopsy-budget/details` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/size-chart-definition` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/stockRecoIngestionDate` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/top-verticals` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/listing/voc-catalog-insight-adoption` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/alphaListing/updateApprovalRequestStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/checkAutofillVerticals` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/create` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/create-variants` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/delete-variants-data` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/draft` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-autofill-external-images-status` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-autoqc-guidelines` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-conditional-mandatory-attributes` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-product-title-preview` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetch-variants-data` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/fetchAutofillAttributes` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/get-fsn-attributes` | WRITE |
| W | GET | `seller.flipkart.com/napi/createProductV2/get-model-vertical-guidelines` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/getPartialDraft` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/predict-vertical` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/save-recommended-vertical` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/save-variants-data` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/submit` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/updatePartial` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/v1/create-variant` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/v1/delete-variants` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/v1/fetch-variant-definition` | WRITE |
| W | GET | `seller.flipkart.com/napi/createProductV2/verticalDefinition` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/createProductV2/verticalDefinitionV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/document/upload` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/create-draft` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/delete-request` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/fetchQCInProgressStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/get-drafts` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/get-summary` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/is-fsn-owner` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/is-fsn-owner-bulk` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/save-draft` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/search` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/edit-product/submit-draft` | WRITE |
| W | GET | `seller.flipkart.com/napi/image-enricher/createDraft` | WRITE |
| W | GET | `seller.flipkart.com/napi/image-enricher/createPayment` | WRITE |
| W | GET | `seller.flipkart.com/napi/image-enricher/saveDraft` | WRITE |
| W | GET | `seller.flipkart.com/napi/image-enricher/submitDraft` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/addToGroup` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/bulk-edit-rate-limit` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/create-update-listings` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/deleteFeed` | WRITE |
| W | GET | `seller.flipkart.com/napi/listing/deleteRequest` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/feed-listings-created/search` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/feed-vc-action` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/feed-vc-predict` | WRITE |
| W | GET | `seller.flipkart.com/napi/listing/image-uploader/images` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/request-download-images-catalog-file` | WRITE |
| W | GET | `seller.flipkart.com/napi/listing/image-uploader/requested-images-catalog-file-download-status` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/image-uploader/save-images` | WRITE |
| W | GET | `seller.flipkart.com/napi/listing/image-uploader/sku` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/instantCatalogUploadStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-price-reco-update` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/lqs-return-reco-update` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/mspEnabled` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/priceUpdateHistory` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/removeFromGroup` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/return-reason-updated-time-duration` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/return-reco-update` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/saveVerticalPredictionsResponse` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/settlement-commissions` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/settlement-commissions-landing-forward-flow-zone` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/stockFileDownloadNUploadHistory` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/stockFileUploadRequestStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/submit-size-chart` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/update-moq-fsp` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/update-size-chart` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/updateInventory` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/updateSellingPrice` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/uploadCatalogFileV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/uploadGroupingFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/uploadStockFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listing/video-context-create` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listingVideos/upload-video-chunk` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/listings-rest/fashion-trends-bulk-upload` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/delete-feed` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/download-history` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/request-error-file` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/request-file` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/requested-error-file-status` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/requested-file-status` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/search` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/upload-file` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-products/bulk-edit/upload-status` | WRITE |

## [[Orders-and-Shipments]]

Order & shipment lifecycle: my-orders, consignments, self-ship, put-lists, dispatch, labels, manifests.  
**140 endpoints** — 56 read-safe · 35 write/export · 49 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/consignment/bulkConsignmentStatus` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getConsignmentDetails` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getConsignmentsList` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getDedicatedSpace` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getFBFAddressByPincode` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getFbfGstinDocumentDetails` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getInwardedListings` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getInwardedQcCount` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getListingPricingInfo` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getPromisableCapacities` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getQCTickets` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getRTDBoxDetails` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/isInvoiceAvailable` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/schedulingEligibility` | READ |
| R | GET | `seller.flipkart.com/napi/consignment/search` | READ |
| R | GET | `seller.flipkart.com/napi/my-orders/getSortedShipments` | READ |
| R | GET | `seller.flipkart.com/napi/my-orders/getUniqueDBD` | READ |
| R | GET | `seller.flipkart.com/napi/putlist/fetchPutlistItems` | READ |
| R | GET | `seller.flipkart.com/napi/putlist/getAllPutlists` | READ |
| R | GET | `seller.flipkart.com/napi/putlist/getBinCapacity` | READ |
| R | GET | `seller.flipkart.com/napi/selfship/getDispatchBulkActionProgress` | READ |
| R | GET | `seller.flipkart.com/napi/selfship/getDropshipVendors` | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadActiveListings` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadBulkErrorFile` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/consignment/downloadConsignmentDetails` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadConsignmentLabel` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadConsignmentListings` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadConsignmentVisibilityDetails` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadEWayBill` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadInvoiceCSV` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadInvoices` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/consignment/downloadPOP` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadQCFile` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadQCTickets` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/consignment/getDownloadListingStatus` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/triggerInvoiceDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/triggerLabelDownload` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/consignment/triggerListingsDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/download-bulk-orders` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/download-errored-bulk-orders` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/label-generation-status` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/print/invoice` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/downloadBulkProofOfPickup` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/downloadManifestPDFV2` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/download_csv_v3` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/download_upcoming_report` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/putlist/downloadFile` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/putlist/downloadPutlist` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/putlist/getFileDownloadStatus` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/putlist/triggerFileDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/selfship/downloadInvoice` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/selfship/download_csv_v3` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/selfship/setDispatchDownloadFlag` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/shipments/v3/download3X5Labels` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/shipments/v3/downloadInvoice` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/shipments/v3/downloadLabels` | READ_FILE |
| ? | UNKNOWN | `seller.flipkart.com/napi/consignment/` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/consignment/dispatchConsignment` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/consignment/markRTD` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fulfilment-rest/self-ship/` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/my-orders/reprint_labels` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/my-orders/revamped-orders-print` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/orders/health_report` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/orders/histories` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/orders/v3/rtsWithScanV2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship-returns/return-pickup` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship/dispatchOrders` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship/markDelivered` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship/markServiced` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship/orders` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship/qrCode` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship/serviceHistories` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/selfship/shipmentHistories` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/shipments/hyperlocalPack` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/shipments/packV2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/shipments/print_labels` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/shipments/print_only_invoices` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/shipments/print_only_labels` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/shipments/rtsV2` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/consignment/getAllSkuListings` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/consignment/getConsignmentSummaryV2` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/consignment/getPickUpSlots` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/consignment/getRecoListings` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/consignment/getSlots` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/consignment/getZonalRecommendedListings` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/my-orders/fetch` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/my-orders/getBarcode` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/my-orders/search` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/my-orders/state-counts` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/orders/fetch` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/orders/fetchV2` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/orders/getGSTRates` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/orders/getGroupedCounts` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/orders/getHandoverCounts` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/orders/getOrdersCountForIntransit` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/orders/search` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/putlist/closePutlist` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/putlist/validateListing` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/selfship-returns/stateCounts` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/selfship/fetch` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/selfship/fetchStateCounts` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/selfship/fetchStateCountsV2` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/selfship/getBulkDispatchActionResult` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/selfship/search` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/shipments/getOTCDetails` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/address/add` | WRITE |
| W | GET | `seller.flipkart.com/napi/consignment/cancel` | WRITE |
| W | GET | `seller.flipkart.com/napi/consignment/cancelPickUp` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/create/empty` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/createConsignmentFromSplits` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/delete` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/deleteConsignmentItem` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/generateSplitForIntent` | WRITE |
| W | PUT | `seller.flipkart.com/napi/consignment/markAsDefaultAddress` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/scheduleConsignment` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/update` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/updateConsignmentAddresses` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/updateConsignmentBoxInfo` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/updateQCTickets` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/updateRTDBoxDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/uploadBulkConsignment` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/uploadEInvoice` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/consignment/uploadEWayBill` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fulfilment-rest/self-ship/reUploadRtoFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/my-orders/bulk-orders-upload-validation` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/my-orders/upload-bulk-orders` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/orders/cancel` | WRITE |
| W | GET | `seller.flipkart.com/napi/orders/downloadLabelsCreatedV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/putlist/addItems` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/putlist/createPutlist` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/putlist/deleteItem` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/putlist/updateLBHW` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/selfship-returns/return-acknowledge` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/selfship-returns/return-cancel` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/selfship/updateShipment` | WRITE |
| W | POST | `seller.flipkart.com/napi/selfship/uploadBulkDispatchFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/selfship_returns/update_tech_visit` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/shipments/cancel` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/shipments/confirmPackStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/shipments/update_form_ack` | WRITE |

## [[Payments-and-Finance]]

Settlements, payments, TDS, partner-master finance data.  
**36 endpoints** — 19 read-safe · 16 write/export · 1 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/partner-master/categories` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/ads` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/banner` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/feedback/factors/` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/feedback/ratings/` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/partner_categories` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/partners/summary` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/quotation/` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/quotes` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v0/service-orchestration/document/list` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/partner_categories/list` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/seller` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/unrated/seller/` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/{quote_id}/seller/audit` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/quotes/{quote_id}/seller/status` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/ratings` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v1/ratings/reviews` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v2/quotes/seller` | READ |
| R | GET | `seller.flipkart.com/napi/partner-master/v2/quotes/seller/cta` | READ |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/getTDSDocument` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics-rest/category-mandate/settlement-file/initiate` | WRITE |
| W | GET | `seller.flipkart.com/napi/metrics-rest/category-mandate/settlement-file/poll` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics-rest/settlement-template-upload/` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics-rest/settlement-updated-file-upload/` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/payments-rest/photoView` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/payments-rest/uploadSpfClaimFile` | WRITE |
| W | GET | `seller.flipkart.com/napi/payments/checkFyReportAvailableV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/payments/downloadSellerStatements` | WRITE |
| W | GET | `seller.flipkart.com/napi/payments/fetchBlockStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/payments/fetchLastPaymentDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/payments/fetchOutstandingPaymentDetails` | WRITE |
| W | GET | `seller.flipkart.com/napi/payments/fetchSellerStatement` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/tds/getClaimEligibilty` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/tds/getClaimHistory` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/tds/getTDSClaimData` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/tds/postTdsUploadData` | WRITE |

## [[Pricing-and-RateCard]]

Price management, price scheduling, rate cards & commission.  
**20 endpoints** — 0 read-safe · 7 write/export · 13 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| ? | UNKNOWN | `seller.flipkart.com/napi/pricing/pendingPriceApprovals` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalHistory` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalSetThreshold` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalThresholds` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/pricing/approvalJobStatus` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/pricing/priceApprovalReviewCycle` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/pricing/reviewAction` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/rate-card/fetch-is-shopsy-fsn` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/rate-card/fetchRateCardFees` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/rate-card/get-complete-category-tree` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/rate-card/getRateCardCategories` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/rate-card/getRateCardSubCategories` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/welcome/fetch-rate-card-fees` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/price-scheduling/priceRuleCreate` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/price-scheduling/priceRuleUpdate` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/pricing/approvePriceApproval` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/pricing/createPriceApprovalJob` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/pricing/disapproveApprovedListings` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/pricing/disapprovePriceApproval` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/pricing/updateLPOverride` | WRITE |

## [[Promotions]]

Flipkart promotion / offer participation surfaces.  
**6 endpoints** — 0 read-safe · 3 write/export · 3 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| ? | UNKNOWN | `seller.flipkart.com/napi/promotions/check-flo-seller` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/myp/get-promotion` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/myp/get-promotions` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/myp/create-promotion` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/myp/enable-disable-promotion` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/sellerPromotions/uploaded-listings-status` | WRITE |

## [[Report-Centre]]

Business/analytics report catalogue — list, count, categories, download; the Seller-Insights / earn-more pipeline.  
**39 endpoints** — 6 read-safe · 21 write/export · 12 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/downloadReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/downloadReport/` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/generatedReportsCount` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generate-report` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateCatalogueReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateConversionReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateInventoryReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateLatchOnReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateOrdersReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateOrdersReportOutput` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generatePriceRecoReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateReturnsReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateSettelmentPriceRecoReport` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generatedReports` | EXPORT |
| R | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/getReportsCount` | READ |
| R | GET | `seller.flipkart.com/napi/metrics/bizReport/report/2/detail` | READ |
| R | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkReports` | READ |
| R | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/getReportsV2` | READ |
| R | GET | `seller.flipkart.com/napi/metrics/bizReport/reportCategories` | READ |
| R | GET | `seller.flipkart.com/napi/metrics/bizReport/reportsNew` | READ |
| ? | UNKNOWN | `seller.flipkart.com/napi/tally-reports/api/reportRequests` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/getReportStatus` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/check-report` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkConversionReports` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkLatchOnReport` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkOrdersReport` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkOrdersReportOutput` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkPriceRecoReport` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkReturnsReport` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkSettelmentPriceRecoReport` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/reports` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/category/generatedReports` | WRITE |
| W | PUT | `seller.flipkart.com/napi/metrics/bizReport/deleteScheduledReport` | WRITE |
| W | PUT | `seller.flipkart.com/napi/metrics/bizReport/editScheduledReport` | WRITE |
| W | GET | `seller.flipkart.com/napi/metrics/bizReport/getScheduledReports` | WRITE |
| W | PUT | `seller.flipkart.com/napi/metrics/bizReport/retryReports` | WRITE |
| W | GET | `seller.flipkart.com/napi/metrics/bizReport/submitReport` | WRITE |

## [[Returns-and-Recall]]

Customer returns, RTO, and product recall workflows.  
**20 endpoints** — 5 read-safe · 4 write/export · 11 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| W-export | UNKNOWN | `seller.flipkart.com/napi/returns/downloadExportReport` | EXPORT |
| W-export | GET | `seller.flipkart.com/napi/returns/fetchExportStatus` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/returns/triggerExport` | EXPORT |
| R | GET | `seller.flipkart.com/napi/returns/requestedStateCounts` | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/recall/downloadFile` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/recall/getDownloadListingStatus` | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/recall/triggerListingsDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/returns/downloadBulkProofOfPickup` | READ_FILE |
| ? | UNKNOWN | `seller.flipkart.com/napi/returns/replenish` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/returns/requested` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/returns/techVisitNotes` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/returns/techVisitNotesImages` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/returnsRecommendations` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/returns/fetchReturnsTotalCount` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/returns/fetchReturnsV2` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/returns/getSPFProductIssueType` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/returns/getSPFProductType` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/returns/primaryReturnsCount` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/returns/searchReturnsV2` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/returns/cancelReturn` | WRITE |

## [[Seller-Misc-Services]]

Assorted seller napi micro-services not owned by another section (telemetry, home widgets, OTP, tracking).  
**62 endpoints** — 7 read-safe · 16 write/export · 39 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/get-locations` | READ |
| R | GET | `seller.flipkart.com/napi/getSellerStoriesDetails` | READ |
| R | GET | `seller.flipkart.com/napi/metrics/darwin/v3/tiering-metrics` | READ |
| R | GET | `seller.flipkart.com/napi/metrics/homePage/goalsDetails` | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/metrics/priceRecoErrorFileDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/metrics/sbpPriceRecoErrorFileDownload` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/smart-inwarding/downloadQCFile` | READ_FILE |
| ? | POST | `seller.flipkart.com/api/send-otp` | UNKNOWN |
| ? | POST | `seller.flipkart.com/api/validate-otp` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/darwin/finalTier` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fdp/batch-events` | UNKNOWN |
| ? | POST | `seller.flipkart.com/napi/metrics/search` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/requestForCallBack` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/tracking/trackReturns` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/voice/translate` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/contextualFaq/getFaqs` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/get-marketing-card` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/getCallBackDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/getRtbbdDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/getQuestionnaire` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/metrics-data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/tiering-metrics` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/get-filters` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/generalRecoCall` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/getImpact` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/getImpactCsv` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/getRUReccomendationCards` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/insightRecommendation` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/oosInsight` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/oosInsightData` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/count` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/filters` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/history` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/recommendationData` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/productDetailsView` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/rsppNotification` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/search/min_max_dates` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/dropShipBreaches` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/packageAdherence` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/recommendations` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/sellerAnalytics/zoneDetailForRU` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/seller-capability/fetch-capability` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/shipping/getShippingFee` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/cancelled_orders/fetchV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/getHomePageUpdates` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/lbhw/updateV2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics-rest/competitor-products/bulk-upload` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/darwin/updateQuetionnaireResponse` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/priceRecommendationUpdate` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/create-rule` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/delete-rule` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/pricing/automation/update-rule` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/insight/updateOosInsightData` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/priceRecoFileUploadRequestStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/sbpPriceRecoFileUploadStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/uploadDocumentImage` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/uploadPriceRecoFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/metrics/uploadPriceRecoSbpFile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/scf/uploadImage` | WRITE |

## [[Seller-QnA-and-UGC]]

Product Q&A and seller-generated content answers.  
**12 endpoints** — 5 read-safe · 2 write/export · 5 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/qnaStore/questions` | READ |
| R | GET | `seller.flipkart.com/napi/qnaStore/questionsV2` | READ |
| R | GET | `seller.flipkart.com/napi/ugc/fetchSellerAnsweredProductIds` | READ |
| R | GET | `seller.flipkart.com/napi/ugc/fetchSellerAnsweredQuestions` | READ |
| R-file | GET | `seller.flipkart.com/napi/qnaStore/getDocumentsMetadata` | READ_FILE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/riddler/fetchSellerQnACount` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ugc/fetchAllAnswersForQuestion` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ugc/fetchAnsweredQuestionsForFSN` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ugc/fetchUnansweredQuestionsForFSN` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ugc/searchAnsweredQuestions` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/qnaStore/submit` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ugc/submitAnswer` | WRITE |

# ADS lane

## [[Flipkart-Ads-and-FSN]]

Flipkart Ads (PLA/PCA campaigns via fed-ads) + Consolidated FSN performance + fkpromo.  
**20 endpoints** — 5 read-safe · 4 write/export · 11 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-darkstore-discount` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-eligible-listings` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-managed-listings` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-mapped-listings` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/fkpromo/download-recommended-listings` | READ_FILE |
| ? | UNKNOWN | `seller.flipkart.com/fed-ads/navbar/seller` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/fed-ads/sellerpoc` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/fed-ads/violet-lms/authenticate` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-opt-in` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-opt-in-mandate` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-opt-out` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-retry-validation` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-file-validation-status` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-file-validation-status-V3` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fkpromo/get-fk-promotion-by-id` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/fkpromo/get-fk-promotions` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/fkpromo/delete-managed-listings` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-update-listings` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fkpromo/fk-promotion-upload-post-opt-in` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/fkpromo/upload-selsub-listings` | WRITE |

# VENDORHUB lane

## [[Vendor-Analytics]]

Sales & inventory analytics: aggregated metrics, purchasing trends, operational performance, product details.  
**7 endpoints** — 2 read-safe · 2 write/export · 3 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| W-export | UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/report` | EXPORT |
| W-export | UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/sales-report` | EXPORT |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/operational-performance` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/purchasing-trends` | READ |
| ?read | UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/aggregated-metrics` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/filter-data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `vendorhub.flipkart.com/vendor/analytics/product-details` | UNKNOWN_READLIKE |

## [[Vendor-Catalog-and-Feeds]]

Cataloging (browse-tree, FSN create, feeds) and QC-norms / BIS compliance feeds.  
**12 endpoints** — 4 read-safe · 4 write/export · 4 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/browse-tree` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/feed-list` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/qc-norms/bis-list` | READ |
| R-file | POST | `vendorhub.flipkart.com/vendor/feeds/download-feed-file` | READ_FILE |
| ? | UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/check-template` | UNKNOWN |
| ? | UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/vertical-attributes` | UNKNOWN |
| ?read | UNKNOWN | `vendorhub.flipkart.com/vendor/feeds/feed-list` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `vendorhub.flipkart.com/vendor/feeds/feed-search` | UNKNOWN_READLIKE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/create-fsn` | WRITE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/feeds/upload-feed-file` | WRITE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/qc-norms/upload-bis-certificates` | WRITE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/qc-norms/upload-feed-file` | WRITE |

## [[Vendor-Config-and-Support]]

Sale config, ticket portal (Freshworks), support mail, recon tool, TaaS migration check.  
**5 endpoints** — 2 read-safe · 1 write/export · 2 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/config/sale-config` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/ticketPortalUrl` | READ |
| ? | UNKNOWN | `vendorhub.flipkart.com/vendor/recon-tool/redirect` | UNKNOWN |
| ?read | UNKNOWN | `vendorhub.flipkart.com/vendor/config` | UNKNOWN_READLIKE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/support/send-mail` | WRITE |

## [[Vendor-Documents]]

Document service: getFile/getDocument downloads, static documents, upload templates.  
**5 endpoints** — 2 read-safe · 2 write/export · 1 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R-file | UNKNOWN | `vendorhub.flipkart.com/vendor-p/download-file/` | READ_FILE |
| R-file | UNKNOWN | `vendorhub.flipkart.com/vendor-p/getFile/v1/retail/documents/` | READ_FILE |
| ? | UNKNOWN | `vendorhub.flipkart.com/vendor-portal/home` | UNKNOWN |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor-p/document-service/v1/retail/documents/upload` | WRITE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor-p/upload/legal-metrology/feed/upload` | WRITE |

## [[Vendor-Payments]]

Vendor payments, debit notes, invoice-debit downloads.  
**2 endpoints** — 1 read-safe · 0 write/export · 1 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `vendorhub.flipkart.com/vendor/accounting/debit-note/` | READ |
| ?read | UNKNOWN | `vendorhub.flipkart.com/vendor/accounting/debit_note/details/id` | UNKNOWN_READLIKE |

## [[Vendor-Platform-Services]]

Retail-palantir request bus, Ryuk document jobs, Triton feed processor — the plumbing under the SPA.  
**8 endpoints** — 1 read-safe · 2 write/export · 5 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `vendorhub.flipkart.com/retail-palantir/v1/request` | READ |
| ? | UNKNOWN | `vendorhub.flipkart.com/api/` | UNKNOWN |
| ? | UNKNOWN | `vendorhub.flipkart.com/ryuk/v1/document/retail_fulfilment_asn_action_history/client_reference_id/` | UNKNOWN |
| ? | UNKNOWN | `vendorhub.flipkart.com/ryuk/v1/document/retail_fulfilment_report/client_reference_id/` | UNKNOWN |
| ? | UNKNOWN | `vendorhub.flipkart.com/triton/v1/feed/clientRefId/` | UNKNOWN |
| ? | POST | `vendorhub.flipkart.com/triton/v1/feed/search` | UNKNOWN |
| W | UNKNOWN | `vendorhub.flipkart.com/ryuk/v1/document/bulk_upload_template/client_reference_id/` | WRITE |
| W | POST | `vendorhub.flipkart.com/triton/v1/feed/processor/upload` | WRITE |

## [[Vendor-Purchase-Orders]]

Vendor Hub 1P purchase orders, PO workbook download, GRN.  
**1 endpoints** — 1 read-safe · 0 write/export · 0 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/purchase-orders-summary` | READ |

## [[Vendor-Returns]]

Return orders summary and RTV for the 1P vendor lane.  
**1 endpoints** — 1 read-safe · 0 write/export · 0 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/return-orders-summary` | READ |

## [[Vendor-Users-and-Access]]

User management, roles & warehouses, UAM authorisation, vendor picker, aggregate entities.  
**14 endpoints** — 10 read-safe · 4 write/export · 0 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/aggregate-entities` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/uam/isResourcesAuthorised` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/profile` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/profile/my` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/roles-and-warehouses` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/user` | READ |
| R | GET | `vendorhub.flipkart.com/vendor/user-management/user-data` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/users/active` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/users/suspended` | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/vendor-list` | READ |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/change-password` | WRITE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/update-user` | WRITE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/user-activation/activate` | WRITE |
| W | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/user-activation/suspend` | WRITE |

# PLATFORM lane

## [[GraphQL-Data-Core]]

The single /napi/graphql gateway — every dashboard widget is a GraphQL operation.  
**2 endpoints** — 1 read-safe · 0 write/export · 1 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | UNKNOWN | `seller.flipkart.com/napi/graphql` | READ |
| ? | UNKNOWN | `seller.flipkart.com/napi/graphql-sse` | UNKNOWN |

## [[Growth-Insights-and-Assistance]]

SIR insights, guided assistance, gamification, GA content, home-page growth widgets.  
**66 endpoints** — 0 read-safe · 22 write/export · 44 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| W-export | GET | `seller.flipkart.com/napi/seller-insightsV2/downloadReport/` | EXPORT |
| W-export | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/report/generateReport` | EXPORT |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/learning-pilot-faqs` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/sample-attachment` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/top-faqs` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga/diagnosis` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga/gaFeedback` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga/issue-types` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga/selectInstanceNodeHelpSection` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/ga/selectInstanceNode_v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/riddler/markQuestionAsNotInterested` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/riddler/notifyAnswerEvent` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/bestseller-product-opportunities-v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/dismiss-product-opportunity` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/msku-recommendations` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/oos-product-opportunities-v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/product-opportunities-impact` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/product-opportunities-v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/report/checkReports` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/shopsy-product-opportunities-v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/supervalue-product-opportunities-v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/trending-product-opportunities-v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/trending_design_recommendations_v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/value-engg-opportunities-v2` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/napi/welcome/send-feedback` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/search-faqs` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/gaSearch_v2` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/get-config-service-data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/get-questionnaires` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/getAssistanceCategories` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/getIssuesForFilter` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/getNodeId` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/getNodeId_v2` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/getSubIssuesForFilter` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/ga/getVideos` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/yoda/actionHistory` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/metrics/yoda/sellerIncentive` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/get-approval-status` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/get-seller-profile` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/msku-attribute-listings-view` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/product-opportunities-filter-values` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/welcome/data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/welcome/get-commission` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/welcome/get-complete-category-tree` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/welcome/get-config-service-data` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/welcome/get-top-sellers-data` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga-content-manager/update-usage` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/createBookmark` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/createIncident_v2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/createInstanceHelpSection` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/createInstance_v2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/deleteBookmark` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/deleteInstance` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/getBookmarks` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/getBulkUploadStatus` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/submitSurvey` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/ga/uploadAttachment` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/riddler/bookmarkQuestion` | WRITE |
| W | GET | `seller.flipkart.com/napi/riddler/fetchAssignedFsnsForSeller` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/riddler/fetchAssignedQuestionsCount` | WRITE |
| W | GET | `seller.flipkart.com/napi/riddler/fetchAssignedQuestionsForProduct` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/bookmark-product-opportunity` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/bookmarks-product-opportunities-v2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/unbookmark-product-opportunity` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/update-seller-intent-msku-opportunities` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/seller-insightsV2/update-seller-profile` | WRITE |

## [[Onboarding-and-SPF]]

Seller onboarding, SPF, partner services.  
**6 endpoints** — 1 read-safe · 3 write/export · 2 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/onboarding/getBranchByIFSC` | READ |
| ?read | UNKNOWN | `seller.flipkart.com/napi/onboarding/fetchAllBankDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/onboarding/taskDetailsFirefly` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/napi/onboarding/generateOtpMobile` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/onboarding/updateBookSellerBusinessDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/onboarding/updateSellerBankDetailsV3` | WRITE |

## [[Printing]]

Label / invoice printing certificate & signature service (health-check path).  
**1 endpoints** — 1 read-safe · 0 write/export · 0 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | UNKNOWN | `seller.flipkart.com/napi/printing/certificate` | READ |

## [[Profile-and-Account]]

Manage profile, multi-seller select, partner permissions, myp account surfaces.  
**76 endpoints** — 10 read-safe · 34 write/export · 32 unknown.

| R/W | METHOD | Host · Path | Class |
|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/manageProfile/cygnetGstin` | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/get-pincode-details` | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getAppSessions` | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getNFBFLocation` | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getSellerAccountDetails` | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getSellerBusinessDetails` | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/getSellerIdentity` | READ |
| R | GET | `seller.flipkart.com/napi/manageProfile/kycGstin` | READ |
| R-file | GET | `seller.flipkart.com/napi/manageProfile/download-document/` | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/myp/download-eligible-listings` | READ_FILE |
| ? | UNKNOWN | `seller.flipkart.com/api/partnerPermissions/checkPartnerAccess` | UNKNOWN |
| ? | UNKNOWN | `seller.flipkart.com/api/partnerPermissions/invokePartnerAccess` | UNKNOWN |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/check-serviceability` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/fieldExists` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-location-rules` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-location-tasks` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-reactivation-clause` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/get-seller-pan` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/getBankDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/getLocationsList` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/getReturnLocations` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/getSellerCalendarDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/getSellerPreference` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/getSellerSettingsDetails` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/goingWithoutGSTin` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/gstinExists` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/partnerSearch` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/requestAMREcallback` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/resendEmailVerification` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/seller-has-gstin` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/validateSellerHoliday` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyEmailOtp` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyMobile` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyOTPSelfServePhone` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/verifyProperty` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/manageProfile/weekly-off-metadata` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/myp/eligible-listings-count` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/myp/get-category-tree` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/myp/get-seller-brands` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/myp/search-by-listing-id` | UNKNOWN_READLIKE |
| ?read | UNKNOWN | `seller.flipkart.com/napi/myp/search-by-sku` | UNKNOWN_READLIKE |
| W | UNKNOWN | `seller.flipkart.com/api/partnerPermissions/deletePartnerAccess` | WRITE |
| W | GET | `seller.flipkart.com/napi/manageProfile/addSellerHoliday` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/create-` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/createRegisteredApplication` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteAccountWithOtp` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteAllAppSession` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteAppSession` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteCalendarHolidays` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteOtherAppSession` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/deleteRegisteredApplication` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/dummyFileUpload-multilocation` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/fileUpload` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/generateOTPSelfServePhone` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/generateOtp` | WRITE |
| W | GET | `seller.flipkart.com/napi/manageProfile/getRegisteredApplications` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/revokeRegisteredApplication` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/rules-confirmation` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/saveLogisticsSetting` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/submitEmailDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/update-gstin-loc-details` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateBankDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateBusinessDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateContactDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateDisplayDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateEmailOtp` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateFADetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateGstin` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateInvoiceAddress` | WRITE |
| W | GET | `seller.flipkart.com/napi/manageProfile/updateOTPSelfServePhone` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updatePocDetails` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateSellerPreference` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateTwoFactorDetails/v2` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/manageProfile/updateWorkingHours` | WRITE |
| W | UNKNOWN | `seller.flipkart.com/napi/myp/delete-uploaded-listings` | WRITE |
