---
title: Invoices
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: stub-to-deep-study
---

# Invoices

JIVO's invoices against Blinkit POs. Report type 'Invoices Excel' filtered by GRN date. Detail route: /app/invoice-details/:vendorInvoiceId/:orderNumber.

## To capture (Phase 1 deep crawl)
- [ ] every subpage / tab / filter
- [ ] data API endpoint(s) + params + response shape (reads only)
- [ ] screenshot

## Connections
- Portal: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Against [[PO-Summary]] · exported via [[Report-Requests]]
