---
title: Flipkart Portal Atlas
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: moc
tags: [flipkart, portal-study, read-only]
---

# Flipkart Portal Atlas — JIVO seller + vendor ecosystem (Wave 1, worker B)

> ⚠️ READ-ONLY study. Corpus harvest + endpoint classification + read-only GET replay of the live
> session. No write, upload, report-enqueue, or export was ever fired against Flipkart. Writes are
> catalogued as out-of-scope contracts only. See [[Read-Only-Guardrails]].

Flipkart is **not one portal** — it is **four distinct surfaces**, two of which JIVO uses daily:

| # | Surface | Host | Auth | JIVO login | Live? |
|---|---|---|---|---|---|
| 1 | **Seller Hub** (3P marketplace) | `seller.flipkart.com` (`/napi/*`) | session cookie jar + `fk-csrf-token` on POST | `ecom8@jivo.in` (sellerId `e56b4e65e27e4162`, "JIVOMART") | **current** |
| 2 | **Flipkart Ads / FSN** | `seller.flipkart.com/fed-ads/*` | same jar + CSRF + `x-aaccount`/`x-tenant` | `ecom8@jivo.in` | **current** |
| 3 | **Vendor Hub** (1P / Flipkart Grocery) | `vendorhub.flipkart.com` (`/vendor/*`, `/vendor-p/*`) | `access_token` JWT (24 h) + `_csrf`↔`x-csrf-token` | `gurvinder@jivo.in`, `infinite@jivo.in` | **current** |
| 4 | Marketplace Seller API (public partner API) | `api.flipkart.net/sellers` | OAuth2 client_credentials → Bearer | — (no client id/secret on disk) | **never used** |

Surfaces 1+2 are the *internal SPA XHR API*; surface 4 is Flipkart's *published partner API*. They
are **different products, not two generations of one** — see the Phase-0 seed intel (`captures/seed-intel.md`) §1.
Surface 4 has never been exercised by JIVO (no credentials exist).

## The two SPAs, structurally

- **Seller Hub** = a webpack app served from `static-assets-web.flixcart.com/fk-sp-static/script/`
  with **30 entry bundles** (one per subsystem) + **6 module-federation remotes**
  (`coe`, `listingsManagement`, `manageProfile`, `preLogin`, `sellerComs`, `selleronboarding`).
  Corpus: 195 distinct JS files.
- **Vendor Hub** = a thin `retailer_hub_shell` (`retail.flixcart.com/www/fk-p-fk-retail-vpp/`) that
  mounts a **Blinx micro-frontend** (`/v0/minified/scripts/manifest.json` → `main-a124d00a.js`,
  4.9 MB). Corpus: 7 distinct JS files. The whole vendor API surface (~55 paths) lives in Blinx.

Harvest: **202 distinct JS files / 70 MB, fully unauthenticated** (Flipkart gates data, not code).
0 × 401/403/429, 0 CAPTCHA, 0 bot-check. See `captures/HARVEST.md`.

## Study status (2026-07-30)

- **968 distinct endpoints catalogued** across 29 sections. Classification (see [[Flipkart-Endpoints]]):
  **216 read-safe** (137 READ + 79 READ_FILE), **330 write/export held out of scope**
  (304 WRITE + 26 EXPORT), **422 UNKNOWN** (method/posture unresolved → denied per G1, fully documented).
- **377 SPA routes enumerated** (281 Seller Hub + 96 Vendor Hub) — see [[Flipkart-Pages-and-Routes]].
- **Live browser WALK of both portals** (read-only, navigation-only) — **37 distinct section
  screenshots** (13 Vendor Hub + 24 Seller Hub), per-page network capture, Amendment-04 non-GET
  audit (122 reads, 0 mutations). Gallery: [[Flipkart-Live-Walk]]. Live numbers in [[Flipkart-Data-Inventory]].
- **9 vendor entities** exist across two logins; 6 enumerated live, all 9 named. See Data Inventory.

## Entity facts (VERIFIED live unless noted)

- **Seller Hub:** `ecom8@jivo.in`, sellerId `e56b4e65e27e4162`, display "JIVOMART". 69 one-time
  reports + 3 repeat report-requests on the account (from JIVO's July `getReportsCount`, UNVERIFIED-today).
- **Vendor Hub — gurvinder@jivo.in:** accountId `ACC20F60245910749BB813F22872E5714426`, tenant `FKI`,
  role Operations Head, **6 vendors**. Currently-selected vendor `VEN23097` JIVO MART PRIVATE LIMITED.
- **Vendor Hub — infinite@jivo.in:** accountId `ACCC6AF17C1930A4F65855A0992EACF02C6`, **3 vendors**
  (token on disk expired — documented, not live).

## Navigation

- Index & meta: [[Flipkart-Endpoints]] · [[Flipkart-Pages-and-Routes]] · [[Flipkart-Data-Model]] ·
  [[Flipkart-Data-Inventory]] · [[Flipkart-Live-Walk]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

### Seller lane (`seller.flipkart.com`)
- [[Report-Centre]] · [[Orders-and-Shipments]] · [[Fulfilment-FBF]] · [[Listings-and-Catalog]] ·
  [[Pricing-and-RateCard]] · [[Inventory-and-Stock]] · [[Payments-and-Finance]] ·
  [[Returns-and-Recall]] · [[Promotions]] · [[Lending-and-Growth-Capital]] · [[Seller-QnA-and-UGC]] ·
  [[Compliance-and-Regulation]] · [[Communications-and-Cases]] · [[Seller-Misc-Services]] · [[Marketplace-Seller-API-unused]]

### Ads lane (`seller.flipkart.com/fed-ads`)
- [[Flipkart-Ads-and-FSN]]

### Vendor Hub lane (`vendorhub.flipkart.com`)
- [[Vendor-Purchase-Orders]] · [[Vendor-Analytics]] · [[Vendor-Catalog-and-Feeds]] ·
  [[Vendor-Payments]] · [[Vendor-Returns]] · [[Vendor-Users-and-Access]] · [[Vendor-Documents]] ·
  [[Vendor-Config-and-Support]] · [[Vendor-Platform-Services]]

### Platform / shell (`seller.flipkart.com`)
- [[GraphQL-Data-Core]] · [[Printing]] · [[Onboarding-and-SPF]] · [[Profile-and-Account]] ·
  [[Growth-Insights-and-Assistance]]
