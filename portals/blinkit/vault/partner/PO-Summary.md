---
title: PO Summary
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: portal-section
tags: [blinkit, partner]
status: stub-to-deep-study
---

# PO Summary

Purchase Orders Blinkit raises to JIVO. Columns seen: PO number, Order Date, PO Qty, PO value, Status (SCHEDULED/UNSCHEDULED/Cancelled), Facility. Actions: Download Bulk PO Data, Filters, Group by, per-row 'PO Summary'. Detail route: /app/po-details/:poNumber.

## To capture (Phase 1 deep crawl)
- [ ] every subpage / tab / filter
- [ ] data API endpoint(s) + params + response shape (reads only)
- [ ] screenshot

## Connections
- Portal: [[Partner-Hub]] · [[00-Blinkit-Atlas]]
- Feeds [[Invoices]] (PO → invoice) and [[Report-Requests]] (Bulk PO Excel)
