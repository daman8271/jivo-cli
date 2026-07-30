---
title: Report-Centre
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Report-Centre

> ⚠️ READ-ONLY. Business/analytics report catalogue — list, count, categories, download; the Seller-Insights / earn-more pipeline.

**Endpoints in this section:** 39 — 6 read-safe (READ/READ_FILE), 21 write/export (out of scope), 12 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/getReportsCount` | — | READ |
| R | GET | `seller.flipkart.com/napi/metrics/bizReport/report/2/detail` | — | READ |
| R | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkReports` | CHECK_API | READ |
| R | UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/getReportsV2` | — | READ |
| R | GET | `seller.flipkart.com/napi/metrics/bizReport/reportCategories` | — | READ |
| R | GET | `seller.flipkart.com/napi/metrics/bizReport/reportsNew` | — | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/category/generatedReports` | generatedReportsFetchApi | WRITE |
| PUT | `seller.flipkart.com/napi/metrics/bizReport/deleteScheduledReport` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/downloadReport` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/downloadReport/` | — | EXPORT |
| PUT | `seller.flipkart.com/napi/metrics/bizReport/editScheduledReport` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/generatedReportsCount` | fetchGeneratedReportsCountApi | EXPORT |
| GET | `seller.flipkart.com/napi/metrics/bizReport/getScheduledReports` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generate-report` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateCatalogueReport` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateConversionReport` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateInventoryReport` | fetchApi | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateLatchOnReport` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateOrdersReport` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateOrdersReportOutput` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generatePriceRecoReport` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateReport` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateReturnsReport` | GENERATE_API | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generateSettelmentPriceRecoReport` | — | EXPORT |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/generatedReports` | generatedReportsFetchApi | EXPORT |
| PUT | `seller.flipkart.com/napi/metrics/bizReport/retryReports` | — | WRITE |
| GET | `seller.flipkart.com/napi/metrics/bizReport/submitReport` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/getReportStatus` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/check-report` | CHECK_API |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkConversionReports` | CHECK_API |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkLatchOnReport` | CHECK_API |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkOrdersReport` | CHECK_API |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkOrdersReportOutput` | CHECK_API |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkPriceRecoReport` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkReturnsReport` | CHECK_API |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/report/checkSettelmentPriceRecoReport` | — |
| UNKNOWN | `seller.flipkart.com/napi/metrics/bizReport/reports` | fetchApiUrl |
| UNKNOWN | `seller.flipkart.com/napi/tally-reports/api/reportRequests` | — |

## PROVEN detail & what JIVO uses this for

Report Centre **is** the Seller-Insights / "earn more" pipeline — growth metrics are delivered as
downloadable Analytics Reports, not a live JSON API (`POST napi/sellerInsights/fetch` and
`POST napi/insights/getData` both 404 — DISPROVEN by JIVO).

**PROVEN-BY-JIVO endpoints (replayed 200 against the live `ecom8@jivo.in` session):**

| Verb | Path | Result | Posture |
|---|---|---|---|
| GET | `napi/metrics/bizReport/reportCategories` | **200 VERIFIED live 2026-07-30** — 5 rows: `5=Fulfilment, 10=Invoices, 9=Listings, 4=Payment, 11=Tax` | READ (no CSRF) |
| GET | `napi/metrics/bizReport/report/checkReports?fileName&from_date&to_date&emailId&sellerId` | 200 → `{request_id, downloadLink{link{url}}}` | READ |
| GET | `napi/metrics/bizReport/downloadReport/earn_more_report.xlsx?token=<request_id>&sellerId` | 200 — 124,669 B, 1,553 rows × 16 cols | READ_FILE |
| POST | `napi/metrics/bizReport/report/getReportsV2` | 200 — 4,990 B, `{report_requests[]}` | READ (POST — not fired here) |
| POST | `napi/metrics/bizReport/getReportsCount` | 200 → `{one_time_reports_count:69, repeat_report_request_count:3}` | READ (POST) |
| GET | `napi/metrics/bizReport/report/generateReport?...` | 200 — **ENQUEUE = EXPORT/WRITE (G2), never fired** | EXPORT |

**Report catalogue vs JIVO usage:** the portal exposes **5 report categories** (Fulfilment,
Invoices, Listings, Payment, Tax), each a family of report types. JIVO's automation pulls only the
**earn_more listings report**. The Tax / Invoice / Payment / Fulfilment report families are unused —
see [[Flipkart-Data-Inventory]] §5.

**Gotchas (PROVEN):** the `checkReports` `downloadLink.link.url` is a `storage.googleapis.com`
presigned URL that **403s `SecurityPolicyViolated — VPC Service Controls`** from any IP outside
Flipkart — always download via the `downloadReport` proxy. `generateReport` is a `GET` but it is an
**enqueue (a WRITE)** — the classic G1 trap that the verb does not reveal the posture.

## Live walk findings (VERIFIED 2026-07-30)

From the live Report Centre page (screenshot `sec-14` in [[Flipkart-Live-Walk]]):
**73 Requested reports · 3 Scheduled**, categories All / Fulfilment / Invoices / Listings / Payment /
Tax with **Type** + **Sub Type** selectors and "Request New Report" (an EXPORT — never fired). This
confirms the 5-category surface live and the requested/scheduled counts.


## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
