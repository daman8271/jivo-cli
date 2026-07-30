---
title: Business Reports & Report Central
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, business-reports-analytics]
status: studied
read_only: true
---

# Business Reports & Report Central

**Portal:** Seller Central (3P) · **Section:** `seller/Business-Reports-Analytics` · **Endpoints catalogued:** 14 (8 read-safe, 7 PROVEN live · 1 out-of-scope · 5 unknown/telemetry)

Business Reports (sales dashboard, detail-page/traffic), Report Central (35 FBA/inventory/payment/sales/removals report types), Brand-insights widget, and the AGL global-store-sales report. Business-reports data itself is a POST (/business-reports/api) held out of scope; the report catalogue + config reads are GET.

## What it looks like (live, this run)

![05 business reports](../seller/sec-05-business-reports.png)
![06 site metrics report](../seller/sec-06-site-metrics-report.png)
![24 reportcentral global store sales](../seller/sec-24-reportcentral-global-store-sales.png)

*Captured live from JIVO Mart's Seller Central session, seller/sec-05-business-reports.png; seller/sec-06-site-metrics-report.png; seller/sec-24-reportcentral-global-store-sales.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /reportcentral/api/v1/getRecentlyVisitedReports | — | READ |
| ✅ | GET | sellercentral.amazon.in · /reportcentral/api/v1/getReportConfigurations | — | READ |
| ✅ | GET | sellercentral.amazon.in · /reportcentral/api/v1/getReportPreferences | — | READ |
| ✅ | GET | sellercentral.amazon.in · /reportcentral/api/v1/getWhatsNewConfiguration | 15 | READ |
| ✅ | GET | sellercentral.amazon.in · /reportcentral/i18n/en-GB.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /reportcentral/i18n/en-IN.json | — | READ_FILE |
| ✅ | GET | sellercentral.amazon.in · /reportcentral/i18n/en-US.json | — | READ_FILE |
| · | GET | sellercentral.amazon.in · /br-insights-widget/{param} | — | READ |

## Response shapes (full field lists, from live capture)

- **`/reportcentral/api/v1/getWhatsNewConfiguration`** (15 fields): `archivedAnnouncements`, `archivedAnnouncements.approver`, `archivedAnnouncements.archived`, `archivedAnnouncements.creator`, `archivedAnnouncements.date`, `archivedAnnouncements.expireDate`, `archivedAnnouncements.link`, `archivedAnnouncements.linkText`, `archivedAnnouncements.linkTextStringId`, `archivedAnnouncements.marketplaces`, `archivedAnnouncements.stringId`, `archivedAnnouncements.text`, `archivedAnnouncements.type`, `archivedAnnouncements.valid`, `currentAnnouncements`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| POST | sellercentral.amazon.in · /br-insightswidget-api | READ_POST | POST-bodied endpoint, read-shaped (G0 forbids POST) |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /br-insights-widget-logger | NOISE |
| ? | sellercentral.amazon.in · /br-insights-widget-metrics | UNKNOWN |
| ? | sellercentral.amazon.in · /business-reports-app-logger | NOISE |
| ? | sellercentral.amazon.in · /business-reports/api | UNKNOWN |
| ? | sellercentral.amazon.in · /reportcentral/AGLGlobalStoreSales/0 | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

