---
title: Swiggy Instamart Pages and Routes
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, routes]
---

# Every page and route in the Swiggy Instamart portal

The bird's-eye view: **every route literal in the SPA**, including the ones no JIVO employee has ever opened. Extracted from the router tables of the shell and all six federated remotes, then walked live where reachable.

**119 route literals** were extracted from the routers, which normalise to **85 distinct canonical routes** across 7 apps (the difference is aliases: `/x` vs `/x/` vs `/x/*`, `_private` layout wrappers, and `${id}` vs `{0}` vs `$id` spellings of the same parameter). Both numbers are given because quoting only the larger one would overstate the surface and only the smaller one would hide the aliases. Walk status per route is in [[../COVERAGE-LEDGER|COVERAGE-LEDGER.md]]; screenshots in [[Swiggy-Instamart-Screenshot-Index]].

## The nav, as the Supply Portal presents it

Read off the live page — this is the vendor lane's own information architecture:

```
PERFORMANCE   Vendor Scores · Facility Level · Item Level
FULFILMENT    Purchase Orders · PO Booking · Goods Received
RETURNS       Purchase Returns · Return To Vendor
INVENTORY     Low Inventory · Stock On Hand · Availability
Finance       Downloads
Help          FAQ
```

## Routes by app


### brand-portal-client (shell)

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/account-select` | YES | — |
| `/employee-login` | YES | — |
| `/login` | YES | — |
| `/login/success` | NO | — |
| `/migration-bridge` | YES | — |

### brandverse (brandverseClient v0.0.7)

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/brandverse` | YES | `/brandverse/`, `/brandverse/*` |
| `/brandverse-app` | NO | — |
| `/brandverse-campaign-metrics` | NO | — |
| `/brandverse-dashboard` | NO | — |
| `/brandverse-header` | NO | — |
| `/brandverse-insights` | NO | — |
| `/brandverse-overview` | NO | — |
| `/brandverse/campaign-metrics` | YES | — |
| `/brandverse/overview` | YES | — |
| `/brandverse:` | NO | — |
| `/brandverseCampaignMetrics` | NO | — |
| `/brandverseClient` | NO | — |
| `/brandverseClient/BrandverseApp` | NO | — |
| `/brandverseClient:0.0.7` | NO | — |
| `/brandverseInsights` | NO | — |
| `/brandverseOverview` | NO | — |

### im-catalog (imCatalogClient v0.1.5)

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/im-catalog` | YES | `/im-catalog/*`, `/im-catalog/_private`, `/im-catalog/_private/` |
| `/im-catalog/approvals` | YES | `/im-catalog/_private/approvals/` |
| `/im-catalog/change-requests/:requestId/edit` | NO | `/im-catalog/_private/change-requests/$requestId/edit/`, `/im-catalog/change-requests/$requestId/edit` |
| `/im-catalog/spin/:spinId/edit-attributes` | NO | `/im-catalog/_private/spin/$spinId/edit-attributes/`, `/im-catalog/spin/$spinId/edit-attributes/` |
| `/im-catalog/update-requests` | NO | `/im-catalog/_private/update-requests/` |
| `/im-catalog:id` | NO | `/im-catalog${i}` |

### im-discounts (imBdpoClient v1.19.0)

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/im-discounts` | YES | `/im-discounts/`, `/im-discounts/*`, `/im-discounts/_private` |
| `/im-discounts/campaign/:id` | NO | `/im-discounts/campaign/{0}` |
| `/im-discounts/campaign/create` | NO | `/im-discounts/_private/campaign/create/` |
| `/im-discounts/feedbacks` | YES | `/im-discounts/_private/feedbacks/` |
| `/im-discounts/performance` | YES | `/im-discounts/_private/performance/` |

### im-sampling (imSamplingClient v0.1.11)

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/im-sampling` | YES | `/im-sampling/*`, `/im-sampling/_private`, `/im-sampling/_private/` |
| `/im-sampling-dashboard` | NO | — |
| `/im-sampling/campaign/:id` | NO | `/im-sampling/_private/campaign/$id/`, `/im-sampling/campaign/$id`, `/im-sampling/campaign/${e}`, `/im-sampling/campaign/{0}` |
| `/im-sampling/campaign/:id/Edit` | NO | `/im-sampling/_private/campaign/$id/Edit/`, `/im-sampling/campaign/$id/Edit` |
| `/im-sampling/campaign/:id/edit` | NO | `/im-sampling/campaign/{0}/edit` |
| `/im-sampling/campaign/create` | NO | `/im-sampling/_private/campaign/create/` |
| `/im-sampling/reports` | YES | `/im-sampling/_private/reports/` |

### im-vendor (imVendorClient v2.2.28)

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/im-vendor` | YES | `/im-vendor/`, `/im-vendor/*` |
| `/im-vendor-dashboard` | NO | — |
| `/im-vendor-dashboard-resources` | NO | — |
| `/im-vendor/availability` | YES | — |
| `/im-vendor/downloads` | YES | — |
| `/im-vendor/faq` | YES | — |
| `/im-vendor/grn` | YES | — |
| `/im-vendor/low-stock` | YES | — |
| `/im-vendor/performance-facility-view` | YES | — |
| `/im-vendor/performance-item-list-view` | YES | — |
| `/im-vendor/performance-vendor-scores` | YES | — |
| `/im-vendor/po-booking` | YES | — |
| `/im-vendor/po-dashboard` | YES | — |
| `/im-vendor/purchase-returns` | YES | — |
| `/im-vendor/rtv` | YES | — |
| `/im-vendor/stock-on-hand` | YES | — |

### im-vendor · LocalBuyingApp

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/im-vendor/local-buying` | YES | `/im-vendor/local-buying/*` |
| `/im-vendor/local-buying/home` | YES | — |
| `/im-vendor/local-buying/login` | NO | — |
| `/im-vendor/local-buying/po-summary` | YES | — |
| `/im-vendor/local-buying/request-summary` | YES | — |
| `/im-vendor/local-buying/review-order` | NO | — |

### instamart (imAdsClient v1.4.128)

| Route | Walked | Aliases in the bundle |
|---|---|---|
| `/instamart` | YES | `/instamart/`, `/instamart/*` |
| `/instamart/:id` | NO | `/instamart/${e}` |
| `/instamart/account-select` | NO | — |
| `/instamart/ads` | YES | — |
| `/instamart/advertisement` | YES | — |
| `/instamart/bdpo` | YES | — |
| `/instamart/campaign` | YES | — |
| `/instamart/campaign/:id` | NO | `/instamart/campaign/${e}`, `/instamart/campaign/${s}`, `/instamart/campaign/{0}` |
| `/instamart/campaign/:id/edit` | NO | `/instamart/campaign/${e}/edit`, `/instamart/campaign/{0}/edit` |
| `/instamart/campaign/:id/edit-1cc` | NO | `/instamart/campaign/${e}/edit-1cc`, `/instamart/campaign/{0}/edit-1cc` |
| `/instamart/campaign/create` | NO | — |
| `/instamart/campaign/create-1cc` | NO | — |
| `/instamart/campaign/list` | YES | — |
| `/instamart/employee-login` | NO | — |
| `/instamart/instamart` | NO | `/instamart/instamart/*` |
| `/instamart/login` | NO | — |
| `/instamart/login/success` | NO | — |
| `/instamart/mock/third-party-login` | NO | — |
| `/instamart/npi` | YES | — |
| `/instamart/reports` | YES | — |
| `/instamart/requisition-orders` | YES | — |
| `/instamart/sales` | YES | — |
| `/instamart/sales-insights` | YES | — |
| `/instamart_new_to_brand` | NO | — |

## Connections

- [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Screenshot-Index]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
