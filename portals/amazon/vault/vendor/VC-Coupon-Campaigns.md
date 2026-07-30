---
title: VC Coupon Campaigns
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Vendor Central (1P)
tags: [amazon, vendor, vc-coupon-campaigns]
status: studied
read_only: true
---

# VC Coupon Campaigns

**Portal:** Vendor Central (1P) · **Section:** `vendor/VC-Coupon-Campaigns` · **Endpoints catalogued:** 2 (2 read-safe, 0 PROVEN live · 0 out-of-scope · 0 unknown/telemetry)

Vendor Powered Coupons — the legacy hz coupon-campaigns surface. The one genuinely GET file download on Vendor Central (per-campaign metrics xlsx, cookie-only auth, 302→signin on expiry).

> No live screenshot — this is Vendor Central (session expired, see [[Auth-and-Access]]) or a non-visual asset layer. Endpoints below are documented from the Phase-0 seed evidence and the static corpus.

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| · | GET | www.vendorcentral.in · /hz/vendor/members/coupon-campaigns/download/{campaignId}/download-met | — | READ |
| · | GET | www.vendorcentral.in · /hz/vendor/members/coupon-campaigns/view/{campaignId}/campaign-metrics | — | READ |

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

_None catalogued in this section._

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

