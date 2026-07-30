---
title: VC Catalog & Products
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Vendor Central (1P)
tags: [amazon, vendor, vc-catalog-products]
status: studied
read_only: true
---

# VC Catalog & Products

**Portal:** Vendor Central (1P) · **Section:** `vendor/VC-Catalog-Products` · **Endpoints catalogued:** 3 (3 read-safe, 0 PROVEN live · 0 out-of-scope · 0 unknown/telemetry)

JIVO's 1P catalog inside Vendor Central — the product detail + mycatalog pages and the prismo CSRF-token endpoint that authorises VC product APIs.

> No live screenshot — this is Vendor Central (session expired, see [[Auth-and-Access]]) or a non-visual asset layer. Endpoints below are documented from the Phase-0 seed evidence and the static corpus.

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| · | GET | www.vendorcentral.in · /hz/vendor/members/products/details | — | READ |
| · | GET | www.vendorcentral.in · /hz/vendor/members/products/mycatalog | — | READ |
| · | GET | www.vendorcentral.in · /hz/vendor/members/products/prismo/api/getcsrftoken | — | READ |

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

_None catalogued in this section._

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

