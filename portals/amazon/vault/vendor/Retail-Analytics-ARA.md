---
title: Retail Analytics (ARA)
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Vendor Central (1P)
tags: [amazon, vendor, retail-analytics-ara]
status: studied
read_only: true
---

# Retail Analytics (ARA)

**Portal:** Vendor Central (1P) · **Section:** `vendor/Retail-Analytics-ARA` · **Endpoints catalogued:** 5 (2 read-safe, 0 PROVEN live · 3 out-of-scope · 0 unknown/telemetry)

Amazon Retail Analytics — the 1P demand+supply datamart JIVO sees as a *vendor selling to Amazon*. Sales (ordered/shipped revenue, units, COGS, customer returns) and Inventory (sourceable OOS %, vendor confirmation rate, net received, open PO qty, receive fill rate, sellable/unsellable on-hand, aged-90 inventory) reports. JIVO's daily cron pulls exactly two of ~13 ARA report types.

> No live screenshot — this is Vendor Central (session expired, see [[Auth-and-Access]]) or a non-visual asset layer. Endpoints below are documented from the Phase-0 seed evidence and the static corpus.

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| · | GET | www.vendorcentral.in · /analytics/dashboard/vendorAnalytics | — | READ |
| · | GET | www.vendorcentral.in · /retail-analytics/dashboard/sales | — | READ |

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| POST | www.vendorcentral.in · /api/retail-analytics/v1/get-report-data | READ_POST | POST-bodied endpoint, read-shaped (G0 forbids POST) |
| POST | www.vendorcentral.in · /api/retail-analytics/v1/list-report-download-workflows | READ_POST | POST-bodied endpoint, read-shaped (G0 forbids POST) |
| POST | www.vendorcentral.in · /api/retail-analytics/v1/request-report-download | WRITE | POST + write-verb token (G1 deny) |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

