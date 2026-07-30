---
title: Returns-and-Recall
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Returns-and-Recall

> ⚠️ READ-ONLY. Customer returns, RTO, and product recall workflows.

**Endpoints in this section:** 20 — 5 read-safe (READ/READ_FILE), 4 write/export (out of scope), 11 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R-file | UNKNOWN | `seller.flipkart.com/napi/recall/downloadFile` | — | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/recall/getDownloadListingStatus` | — | READ_FILE |
| R-file | GET | `seller.flipkart.com/napi/recall/triggerListingsDownload` | — | READ_FILE |
| R-file | UNKNOWN | `seller.flipkart.com/napi/returns/downloadBulkProofOfPickup` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/returns/requestedStateCounts` | fetchApi | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/returns/cancelReturn` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/returns/downloadExportReport` | — | EXPORT |
| GET | `seller.flipkart.com/napi/returns/fetchExportStatus` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/returns/triggerExport` | fetchApi | EXPORT |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/metrics/returnsRecommendations` | — |
| UNKNOWN | `seller.flipkart.com/napi/returns/fetchReturnsTotalCount` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/returns/fetchReturnsV2` | — |
| UNKNOWN | `seller.flipkart.com/napi/returns/getSPFProductIssueType` | url |
| UNKNOWN | `seller.flipkart.com/napi/returns/getSPFProductType` | url |
| UNKNOWN | `seller.flipkart.com/napi/returns/primaryReturnsCount` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/returns/replenish` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/returns/requested` | — |
| UNKNOWN | `seller.flipkart.com/napi/returns/searchReturnsV2` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/returns/techVisitNotes` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/returns/techVisitNotesImages` | fetchApi |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
