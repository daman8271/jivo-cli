---
title: Swiggy Instamart Portal Atlas
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: moc
tags: [swiggy, instamart, portal-study, read-only]
---

# Swiggy Instamart Portal Atlas — JIVO brand + supply ecosystem

> ⚠️ **READ-ONLY study.** Corpus harvest + live navigation + screenshots + network capture only.
> Nothing was created, changed, approved, generated, uploaded or deleted. See
> [[Read-Only-Guardrails]] for the auditable form of that claim.

## What this portal actually is

`partner.instamart.in` is **one React SPA that is two portals**. The `/account-select` screen
states it outright: *"Welcome ecom1, You can access both the Brand and Supply portal from below."*

Structurally it is a **webpack module-federation shell** — `brand-portal-client`, federation host
name `partnerHost` — that mounts **six remotes at runtime**. The remote registry is a literal in
the shell's app chunk, which is how all six were found:

| Remote | basePath | Version | What it is | Data host |
|---|---|---|---|---|
| `imAdsClient` | `/instamart` | 1.4.128 | Ads, sales, sales-insights, campaigns, reports, NPI | `partner-api` + `brand-portal-service-http` |
| `imVendorClient` | `/im-vendor` | 2.2.28 | **The Supply Portal** — POs, PO booking, GRN, RTV, returns, stock, availability, vendor performance | **`picker.swiggy.com`** |
| 37 | `/im-discounts` | 1.19.0 | Brand-funded discount campaigns (BDPO) | `brand-portal-service-http` (INFERRED) |
| `brandverseClient` | `/brandverse` | 0.0.7 | Cross-surface Swiggy brand campaigns | `brand-portal-service-http` `/api/v1/3p/` |
| `imSamplingClient` | `/im-sampling` | 0.1.11 | Product-sampling campaigns | `brand-portal-service-http` |
| `imCatalogClient` | `/im-catalog` | 0.1.5 | Product catalogue + SPIN change-request workflow | `brand-portal-service-http` |

Remote entries are versioned assets:
`instamart-media-assets.swiggy.com/brand-portal-client/<basePath>/v<major_minor_patch>_remoteEntry.js`.

### The four production API hosts

| Host | Role | Endpoints |
|---|---|---|
| `brand-portal-service-http.swiggy.com` | `brandPortalServiceBasePath` — ads, sales, catalog, brandverse | 65 |
| **`picker.swiggy.com`** | `scmAPIGatewayBasePath` + `movementPlanningAPIGatewayBasePath` — **the entire supply lane** | 37 |
| `partner-api.swiggy.com` | `partnerServiceBasePath` — accounts, configs, campaign, reports-v2, server clock | 25 |
| `ozone-idp-brands-im-kba.swiggy.com` | ozone IdP, BRAND pool — login/OTP/refresh/signout (all WRITE) | 7 |

### Report-delivery buckets (S3, presigned — the presign is the auth)

| Bucket | Serves |
|---|---|
| `im-brand-reports-in-west.s3.ap-south-1.amazonaws.com` | ads-lane reports: the IM sales xlsx and the ads summary CSVs |
| `scm-procurement-mumbai.s3.ap-south-1.amazonaws.com` | **vendor-lane** exports: item inventory, GRN and PO CSVs (`/inventory-downloads/csv/`) |

Both were reached by plain unauthenticated `GET` of a presigned URL for a report a JIVO user had
**already generated** — a read. Neither bucket appears in the mission brief, and the second one
was not previously known to JIVO's tooling at all.

> **`picker.swiggy.com` is a new discovery.** It appears nowhere in JIVO's existing automation,
> documentation or CLIs. The whole supply/vendor lane — every PO, GRN, return, stock and vendor-
> performance surface — lives on it and JIVO has never read a byte from it. See
> [[Purchase-Orders]] and [[Stock-On-Hand-and-Low-Stock]].

## Corrections to the mission brief (all VERIFIED live)

| Brief said | Reality |
|---|---|
| `partner.swiggy.com` = partner portal shell | **No.** It 302s to `/food/` and serves the *Swiggy Partner App* — the restaurant portal, a different product. The Instamart shell is `partner.instamart.in`. |
| `brands-im-kba.swiggy.com` = Instamart KBA | **Does not resolve** (NXDOMAIN). The real host is `ozone-idp-brands-im-kba.swiggy.com`, the identity provider. |
| `brand-reports-in-west.s3…` | Actual bucket is **`im-brand-reports-in-west.s3.ap-south-1.amazonaws.com`**. |
| — | `picker.swiggy.com` was not in the brief at all and carries 37 endpoints. |

## Study status

**28 section notes · 134 distinct endpoint contracts · 119 route literals · 170 screenshots ·
5 live walk passes.** Classification: **76 read-safe** (75 READ + 1 READ_FILE),
**40 held out of scope** (32 WRITE + 8 EXPORT), **18 UNKNOWN** (documented in
full, denied per G1). **76** reads have a proven method and are wired into the CLI.

Coverage per route is in [[../COVERAGE-LEDGER|COVERAGE-LEDGER.md]]; live counts are in
[[Swiggy-Instamart-Data-Inventory]]; the audit is in [[Study-Verification]].

## Entity facts

`ecom1@jivo.in` (user 345) holds **three** accounts — all three were walked separately, because a
single-account walk drops most of the data:

| Account | Account id | Campaigns | Cities w/ sales | Products w/ sales | Catalog SPINs |
|---|---|---|---|---|---|
| **Jivo Wellness** | `c9f24655-…` | **27** | **132** | 37 | 43 |
| **Jivo Mart Pvt. Ltd** | `89bafc9c-…` | 0 | **22** | 12 | 9 |
| **Jivo** (brand under Wellness) | `260921c1-…` | 0 | 132 | 37 | 43 |

Auth: Bearer JWT + **HMAC request signing**, and `Abacus-Token` instead of `authorization` on the
vendor lane. Full model in [[Auth-and-Access]].

## What JIVO's automation covers today

`~/ecomcliauto/` pulls **one** report — the Instamart sales xlsx — twice a day (flows 9 and 10,
Mart and Wellness), into one table. That is it. Measured against this map:

- the **entire supply lane** (`picker.swiggy.com`, 37 endpoints, 10 sections) — untouched
- **sales-insights** with 47 metric types and 17 dimensions — 2 metrics used
- **campaigns, brand-insights, keywords, creatives, requisition orders** — untouched
- **catalog, sampling, brandverse, discounts** remotes — untouched
- an in-portal **AI assistant** nobody knew existed — untouched

## Navigation

- Index & meta: [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] ·
  [[Swiggy-Instamart-Data-Inventory]] · [[Swiggy-Instamart-Pages-and-Routes]] ·
  [[Swiggy-Instamart-Screenshot-Index]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]] ·
  [[Study-Verification]]

### Supply lane — `imVendorClient` on `picker.swiggy.com` (10 sections)
[[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] ·
[[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] ·
[[Availability-and-Fill-Rate]] · [[Vendor-Performance-Scores]] · [[Vendor-Downloads]] ·
[[Local-Buying]] · [[Vendor-FAQ-Help]]

### Ads lane — `imAdsClient` (10 sections)
[[Sales-Reports]] · [[Sales-Insights]] · [[Ad-Campaigns]] · [[Brand-Insights-Metrics]] ·
[[Keyword-And-Bid-Suggestions]] · [[Creatives]] · [[Requisition-Orders]] ·
[[Products-And-SPINs]] · [[Ads-AI-Chat]] · [[NPI-New-Product-Introduction]]

### Other brand remotes (4 sections)
[[Discounts-BDPO]] · [[Sampling-Campaigns]] · [[Brandverse]] · [[Catalog-SPIN-Management]]

### Platform / shell (4 sections)
[[Accounts-And-Entities]] · [[Config-And-Feature-Flags]] · [[Auth-Sessions-And-Login]] ·
[[Telemetry-And-Third-Party]]
