---
title: Zepto Portal Atlas
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: moc
tags: [zepto, portal-study, read-only]
---

# Zepto Portal Atlas — JIVO seller ecosystem (goal #83)

> ⚠️ READ-ONLY study. Corpus harvest + endpoint classification + gentle GET-probes only. No write, upload, or export is ever fired against Zepto — those are catalogued as out-of-scope contracts, nothing more.

Unlike Blinkit's two-portal split, JIVO's Zepto presence is **one single-page app** at `brands.zepto.co.in` that stitches three module-federation remotes into one shell and fans out to **7 API backends** behind a single JWT.

## Portal structure

| Layer | What it is | Detail |
|---|---|---|
| **Host** | `brands.zepto.co.in` | One SPA, one login (`ecom1@jivo.in`), one JWT sent in the `authorization` header (no `Bearer` prefix). WAF present but not enforced on these reads. |
| **root-shell-631** | Module-federation host shell | Layout, nav, config, file service, support, commons — the frame every remote mounts into. See [[Platform-Common]]. |
| **vendor-635** | Vendor / supply-side remote | POs, ASN, RTV, catalog, stock, invoicing, contracts, payments, ledger, receivables, FBZ. The 13 vendor-lane sections. |
| **ads-632** | Ads / demand-side remote | Brands, creatives, campaigns, wallet, analytics, insights, engagement. The 7 ads-lane sections. |

### The 7 API backends

| Backend host | Serves |
|---|---|
| `fcc.zepto.co.in` | Vendor reports + `/ads-bff` ads BFF — the workhorse; most section traffic lands here |
| `auth-backend.zepto.co.in` | Identity, access-management, subscription, KYC, brands, config |
| `financenew.zepto.co.in` | Finance — receivables, ledger |
| `scpfin.zepto.co.in` | Supply-chain finance |
| `brands-onboarding.zepto.co.in` | Onboarding, KYC |
| `ads-platform.zepto.co.in` | Ads platform |
| `partner.zepto.co.in` | Partner |

## Study status

> **25 sections mapped · 741 endpoint literals catalogued across the JS corpus** — of which **304 classified read-safe** (263 READ + 41 READ_FILE), **141 held out of scope** (82 WRITE + 59 EXPORT), and **296 UNKNOWN** (method unresolved from the minified source, treated as write-until-proven). Splits pulled from `captures/js/sections.json` `read_write` fields; the flat deduped list lives in `captures/js/endpoints-raw.json`.

## Entity facts

- **Entity:** Jivo Wellness Pvt. Ltd. — Manufacturer, STANDARD tier
- **manufacturer_id:** `946950b7-1ce2-4bdf-a7c4-37499e3f5f34`
- **Ads brand_id:** `b3550d5d-fc71-47b0-af4f-f221f909b936`
- **Login:** `ecom1@jivo.in`
- **Auth:** one JWT in the `authorization` header, no `Bearer` prefix — see [[Auth-and-Access]]

## Method

Harvest the on-disk JS corpus (three module-federation remotes) → cluster endpoint literals by host + path prefix into 25 sections → classify each by HTTP method into READ / READ_FILE / WRITE / EXPORT / UNKNOWN → gentle GET-probe only the read-safe ones → write one Obsidian note per section → weave the endpoint index, data model, and guardrail notes → 0 broken links → then extend the read-only CLI. Never a write; see [[Read-Only-Guardrails]].

## Existing CLI coverage

`zepto-cli` already covers **SALES**, **INVENTORY**, and the ads **2×2** (products/brands × range/daily) — the other **~21 sections** are read-only CLI expansion backlog.

## Navigation

- Index & meta: [[Zepto-Endpoints]] · [[Zepto-Data-Model]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]

### Vendor (vendor-635)
- [[Purchase-Orders]] · [[ASN]] · [[Release-Orders-Amendment-Requests]] · [[RTV]] · [[Catalog-Health]] · [[Stock-View-Inventory]] · [[Vendor-Reports-Queue]] · [[Invoicing]] · [[Vendor-Contracts-Margins]] · [[Payments]] · [[Ledger-Recon-Upload]] · [[Receivables]] · [[Fulfilled-by-Zepto]]

### Ads (ads-632)
- [[Brands-Audiences]] · [[Creative-Management]] · [[Ads-Campaigns-Booking-Keywords]] · [[Ads-Billing-Wallet]] · [[Brand-Analytics]] · [[Market-Geo-Consumer-Insights]] · [[Engagement]]

### Platform (root-shell-631)
- [[KYC-Onboarding]] · [[Users-Access]] · [[Subscription-Billing]] · [[Auth-Identity]] · [[Platform-Common]]
