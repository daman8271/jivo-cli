---
title: Platform Common
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, platform, platform-common]
status: studied
read_only: true
---

# Platform Common

**Portal:** Seller Central (3P) · **Section:** `platform/Platform-Common` · **Endpoints catalogued:** 34 (4 read-safe, 0 PROVEN live · 7 out-of-scope · 23 unknown/telemetry)

Cross-cutting platform plumbing shared by every micro-frontend — global search, favourites (trim), notifications, weblab/treatment flags (telemetry, held as NOISE), CSRF-token mints, and generic config.

## What it looks like (live, this run)

![03 global search](../platform/sec-03-global-search.png)

*Captured live from JIVO Mart's Seller Central session, platform/sec-03-global-search.png (each with a paired `.har.json` network log).*

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| · | GET | sellercentral.amazon.in · /draft/dashboard | — | READ |
| · | GET | sellercentral.amazon.in · /draft/registration/dashboard | — | READ |
| · | GET | sellercentral.amazon.in · /gp/satisfaction/survey-form-frame.html | — | READ |
| · | GET | sellercentral.amazon.in · /gp/satisfaction/survey-submit.html | — | READ |

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| ? | sellercentral.amazon.in · /draft/dashboard/savedbyyou | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /edit/bulk | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /edit/bulk/sph | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /edit/handmade | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /featureOverride | WRITE | write-verb constant/path token (G1: deny) |
| ? | sellercentral.amazon.in · /goblin/write | WRITE | write-verb constant/path token (G1: deny) |
| POST | sellercentral.amazon.in · /pulse/v1/question | READ_POST | app-issued POST read (GraphQL/RPC) — G0 forbids POST, gate k |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /1/batch/1/OE/ | NOISE |
| POST | unagi.amazon.in · /1/events/com.amazon.csm.csa.prod | NOISE |
| POST | unagi.amazon.in · /1/events/com.amazon.csm.customsg.prod | NOISE |
| POST | unagi.amazon.in · /1/events/com.amazon.csm.nexusclient.prod | NOISE |
| ? | sellercentral.amazon.in · /1/remote-weblab-triggers/1/OE/ | NOISE |
| ? | sellercentral.amazon.in · /ah/eligibility | UNKNOWN |
| ? | sellercentral.amazon.in · /coupon-details-page | UNKNOWN |
| ? | sellercentral.amazon.in · /globalsearch/v1/search | UNKNOWN |
| ? | sellercentral.amazon.in · /goblin/read | UNKNOWN |
| ? | sellercentral.amazon.in · /gp/search | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/vendor/ | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/vendor/members/help/embed/training/widget/layout/{param}/tag | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/vendor/members/products/details | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/vendor/members/products/mycatalog | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/vendor/members/products/prismo/api/getcsrftoken | UNKNOWN |
| ? | sellercentral.amazon.in · /hz/vendor/{param}/help/embed/{param} | UNKNOWN |
| ? | sellercentral.amazon.in · /ping | NOISE |
| ? | sellercentral.amazon.in · /pix-gateway | UNKNOWN |
| ? | sellercentral.amazon.in · /reorder-coupons-dashboard-page | UNKNOWN |
| ? | sellercentral.amazon.in · /spl/logger | NOISE |
| POST | sellercentral.amazon.in · /tricorder/decide/ | NOISE |
| POST | sellercentral.amazon.in · /tricorder/e/ | NOISE |
| ? | sellercentral.amazon.in · /tricorder/logger | NOISE |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

