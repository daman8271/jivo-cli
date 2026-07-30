---
title: Orders-and-Shipments
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Orders-and-Shipments

> ⚠️ READ-ONLY. Order & shipment lifecycle: my-orders, consignments, self-ship, put-lists, dispatch, labels, manifests.

**Endpoints in this section:** 140 — 56 read-safe (READ/READ_FILE), 35 write/export (out of scope), 49 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/consignment/bulkConsignmentStatus` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadActiveListings` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadBulkErrorFile` | — | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/consignment/downloadConsignmentDetails` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadConsignmentLabel` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadConsignmentListings` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadConsignmentVisibilityDetails` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadEWayBill` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadInvoiceCSV` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadInvoices` | — | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/consignment/downloadPOP` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadQCFile` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/downloadQCTickets` | QC_TICKETS | READ_FILE |
| R | GET | `seller.flipkart.com/napi/consignment/getConsignmentDetails` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getConsignmentsList` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getDedicatedSpace` | — | READ |
| R-file | GET | `seller.flipkart.com/napi/consignment/getDownloadListingStatus` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/consignment/getFBFAddressByPincode` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getFbfGstinDocumentDetails` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getInwardedListings` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getInwardedQcCount` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getListingPricingInfo` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getPromisableCapacities` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getQCTickets` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/getRTDBoxDetails` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/isInvoiceAvailable` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/schedulingEligibility` | — | READ |
| R | GET | `seller.flipkart.com/napi/consignment/search` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/triggerInvoiceDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/consignment/triggerLabelDownload` | — | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/consignment/triggerListingsDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/download-bulk-orders` | downloadApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/download-errored-bulk-orders` | downloadApi | READ_FILE |
| R | GET | `seller.flipkart.com/napi/my-orders/getSortedShipments` | — | READ |
| R | GET | `seller.flipkart.com/napi/my-orders/getUniqueDBD` | — | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/label-generation-status` | fetchApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/my-orders/print/invoice` | downloadApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/downloadBulkProofOfPickup` | downloadApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/downloadManifestPDFV2` | downloadApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/download_csv_v3` | downloadApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/orders/download_upcoming_report` | downloadApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/putlist/downloadFile` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/putlist/downloadPutlist` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/putlist/fetchPutlistItems` | — | READ |
| R | GET | `seller.flipkart.com/napi/putlist/getAllPutlists` | — | READ |
| R | GET | `seller.flipkart.com/napi/putlist/getBinCapacity` | — | READ |
| R-file | GET | `seller.flipkart.com/napi/putlist/getFileDownloadStatus` | — | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/putlist/triggerFileDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/selfship/downloadInvoice` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/selfship/download_csv_v3` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/selfship/getDispatchBulkActionProgress` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/selfship/getDropshipVendors` | fetchApi | READ |
| R-file | UNKNOWN | `seller.flipkart.com/napi/selfship/setDispatchDownloadFlag` | updateApi | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/shipments/v3/download3X5Labels` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/shipments/v3/downloadInvoice` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/shipments/v3/downloadLabels` | — | READ_FILE |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/consignment/address/add` | — | WRITE |
| GET | `seller.flipkart.com/napi/consignment/cancel` | — | WRITE |
| GET | `seller.flipkart.com/napi/consignment/cancelPickUp` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/create/empty` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/createConsignmentFromSplits` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/delete` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/deleteConsignmentItem` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/generateSplitForIntent` | — | WRITE |
| PUT | `seller.flipkart.com/napi/consignment/markAsDefaultAddress` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/scheduleConsignment` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/update` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/updateConsignmentAddresses` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/updateConsignmentBoxInfo` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/updateQCTickets` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/updateRTDBoxDetails` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/uploadBulkConsignment` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/uploadEInvoice` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/consignment/uploadEWayBill` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fulfilment-rest/self-ship/reUploadRtoFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/bulk-orders-upload-validation` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/upload-bulk-orders` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/orders/cancel` | updateApi | WRITE |
| GET | `seller.flipkart.com/napi/orders/downloadLabelsCreatedV2` | downloadApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/putlist/addItems` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/putlist/createPutlist` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/putlist/deleteItem` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/putlist/updateLBHW` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/selfship-returns/return-acknowledge` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/selfship-returns/return-cancel` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/selfship/updateShipment` | updateApi | WRITE |
| POST | `seller.flipkart.com/napi/selfship/uploadBulkDispatchFile` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/selfship_returns/update_tech_visit` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/shipments/cancel` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/shipments/confirmPackStatus` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/shipments/update_form_ack` | updateApi | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/consignment/` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/dispatchConsignment` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/getAllSkuListings` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/getConsignmentSummaryV2` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/getPickUpSlots` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/getRecoListings` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/getSlots` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/getZonalRecommendedListings` | — |
| UNKNOWN | `seller.flipkart.com/napi/consignment/markRTD` | — |
| UNKNOWN | `seller.flipkart.com/napi/fulfilment-rest/self-ship/` | — |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/fetch` | — |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/getBarcode` | — |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/reprint_labels` | downloadApi |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/revamped-orders-print` | — |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/search` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/my-orders/state-counts` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/fetch` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/fetchV2` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/getGSTRates` | — |
| UNKNOWN | `seller.flipkart.com/napi/orders/getGroupedCounts` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/getHandoverCounts` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/getOrdersCountForIntransit` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/health_report` | fetchAPI |
| UNKNOWN | `seller.flipkart.com/napi/orders/histories` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/search` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/orders/v3/rtsWithScanV2` | — |
| UNKNOWN | `seller.flipkart.com/napi/putlist/closePutlist` | — |
| UNKNOWN | `seller.flipkart.com/napi/putlist/validateListing` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship-returns/return-pickup` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/selfship-returns/stateCounts` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/selfship/dispatchOrders` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship/fetch` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship/fetchStateCounts` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship/fetchStateCountsV2` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship/getBulkDispatchActionResult` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship/markDelivered` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/selfship/markServiced` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/selfship/orders` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship/qrCode` | — |
| UNKNOWN | `seller.flipkart.com/napi/selfship/search` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/selfship/serviceHistories` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/selfship/shipmentHistories` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/shipments/getOTCDetails` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/shipments/hyperlocalPack` | — |
| UNKNOWN | `seller.flipkart.com/napi/shipments/packV2` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/shipments/print_labels` | downloadApi |
| UNKNOWN | `seller.flipkart.com/napi/shipments/print_only_invoices` | — |
| UNKNOWN | `seller.flipkart.com/napi/shipments/print_only_labels` | — |
| UNKNOWN | `seller.flipkart.com/napi/shipments/rtsV2` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
