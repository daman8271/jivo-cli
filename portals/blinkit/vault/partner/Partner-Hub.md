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

## Sections — all 11 studied (2026-07-24)
| # | Section | Note | What it is |
|---|---|---|---|
| 1 | PO Summary | [[PO-Summary]] | POs Blinkit raises to JIVO (number, date, qty, value, status, facility) |
| 2 | Appointments | [[Appointments]] | inbound delivery-slot scheduling per PO (internal "PO Scheduling") |
| 3 | Invoices | [[Invoices]] | GRNs + vendor invoices booked against POs (GRN data from Apr 2023) |
| 4 | Payments | [[Payments]] | settlement view: payouts, deductions, Fees & Charges, UTR |
| 5 | Report Requests | [[Report-Requests]] | async report queue (Sales / SOH / Invoices / Bulk PO) |
| 6 | Sales | [[Sales]] | secondary sales / sell-out (item × city × date) |
| 7 | Stock on Hand | [[Stock-on-Hand]] | live inventory (SOH) at Blinkit facilities |
| 8 | Score Card | [[Score-Card]] | performance metrics (fill rate, ranking, potential loss) |
| 9 | Consumer Offers | [[Consumer-Offers]] | brand-fund price offers funded per SKU × city |
| 10 | Assortment | [[Assortment]] | listed / active SKUs per facility |
| 11 | EDI Integration | [[EDI-Integration]] | EDI/API activation (POs, ASNs, invoices) + API-reference viewer |

Plus: My Profile, Help & Support. Existing narrow CLI: `blinkit-cli` (Sales, SOH, Reports, PO/Invoice reads).

## Cross-section references
- [[Partner-Endpoints]] — master API index: ~90 endpoint contracts across all 11 sections (read-safe vs write/export split).
- [[Partner-Data-Model]] — how the sections join (PO number · facility · SKU · date · invoice id) into one relational graph.
