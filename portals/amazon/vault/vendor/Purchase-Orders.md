---
title: Purchase Orders (1P)
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Vendor Central (1P)
tags: [amazon, vendor, purchase-orders]
status: studied
read_only: true
---

# Purchase Orders (1P)

**Portal:** Vendor Central (1P) · **Section:** `vendor/Purchase-Orders` · **Endpoints catalogued:** 8 (5 read-safe, 0 PROVEN live · 3 out-of-scope · 0 unknown/telemetry)

Amazon's inbound POs to JIVO as a vendor — the PO Management service (a separate host+auth from ARA). The 4-step async export (generate → status → download → presigned S3) yields the PO line-item file JIVO's cron ingests. Plus the shared-homepage PO widgets (confirmation, ASN discrepancies, recently-modified).

> No live screenshot — this is Vendor Central (session expired, see [[Auth-and-Access]]) or a non-visual asset layer. Endpoints below are documented from the Phase-0 seed evidence and the static corpus.

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| · | GET | www.vendorcentral.in · /po-api/vendor/homepage/homepage-asn-discrepancies | — | READ |
| · | GET | www.vendorcentral.in · /po-api/vendor/homepage/homepage-confirmation | — | READ |
| · | GET | www.vendorcentral.in · /po-api/vendor/homepage/homepage-recently-modified | — | READ |
| · | GET | www.vendorcentral.in · /po/vendor/members/po-mgmt/dashboard | — | READ |
| · | GET | www.vendorcentral.in · /po/vendor/members/po-mgmt/managepos | — | READ |

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| POST | www.vendorcentral.in · /po-api/vendor/members/po-mgmt/search/downloadVendorSearchFile | READ_POST | POST-bodied endpoint, read-shaped (G0 forbids POST) |
| POST | www.vendorcentral.in · /po-api/vendor/members/po-mgmt/search/generateVendorSearchFile-v | WRITE | POST + write-verb token (G1 deny) |
| POST | www.vendorcentral.in · /po-api/vendor/members/po-mgmt/search/getVendorSearchFileStatus | READ_POST | POST-bodied endpoint, read-shaped (G0 forbids POST) |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

