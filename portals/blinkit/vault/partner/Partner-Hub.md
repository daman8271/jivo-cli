---
title: Blinkit Partner Portal (PartnersBiz)
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: hub
tags: [blinkit, partner, portal-study]
---

# Partner Portal — partnersbiz.com/app

The supply-side portal: Blinkit's POs to JIVO, JIVO's invoices, inventory at Blinkit, sell-out, and performance. Auth: email-OTP → session token (`blinkit-login.sh`, unattended). Back to [[00-Blinkit-Atlas]].

## Sections (sidebar nav, captured 2026-07-24)
| # | Section | Note | What it is |
|---|---|---|---|
| 1 | PO Summary | [[PO-Summary]] | POs Blinkit raises to JIVO (number, date, qty, value, status, facility) |
| 2 | Invoices | [[Invoices]] | JIVO's invoices against POs (GRN date, invoice excel) |
| 3 | Report Requests | [[Report-Requests]] | async report queue (Sales / SOH / Invoices / Bulk PO) |
| 4 | Sales | [[Sales]] | secondary sales / sell-out |
| 5 | Stock on Hand | [[Stock-on-Hand]] | inventory (SOH) at Blinkit facilities |
| 6 | Score Card | [[Score-Card]] | performance metrics (fill rate etc.) |
| 7 | Consumer Offers | [[Consumer-Offers]] | promotions / offers funded |
| 8 | Assortment | [[Assortment]] | listed / active SKUs per facility |
| 9 | EDI Integration | [[EDI-Integration]] | electronic data interchange setup |

Plus: My Profile, Help & Support. Existing narrow CLI: `blinkit-cli` (Sales, SOH, Reports, PO/Invoice reads).
