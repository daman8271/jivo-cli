---
title: Global Selling & Marketplace
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
portal: Seller Central (3P)
tags: [amazon, seller, global-selling-expansion]
status: studied
read_only: true
---

# Global Selling & Marketplace

**Portal:** Seller Central (3P) · **Section:** `seller/Global-Selling-Expansion` · **Endpoints catalogued:** 11 (5 read-safe, 2 PROVEN live · 1 out-of-scope · 5 unknown/telemetry)

Global-selling / build-international-listings — marketplace switcher, exchange rates, listing-preferences, ASIN-translation, global-listings-expansion data, and the account switcher that enumerates which merchant+marketplace this login can reach.

> No live screenshot — this is Vendor Central (session expired, see [[Auth-and-Access]]) or a non-visual asset layer. Endpoints below are documented from the Phase-0 seed evidence and the static corpus.

## Read endpoints (allowlist)

| Live | Method | Host · Path | Fields | Class |
|---|---|---|---|---|
| ✅ | GET | sellercentral.amazon.in · /account-switcher/global-and-regional-account/merchantMarketplace | 18 | READ |
| ✅ | GET | sellercentral.amazon.in · /meld/mons-api/GetMarketplaceSwitcher | 27 | READ |
| · | GET | sellercentral.amazon.in · /account-switcher/dropdown-assets-loader.js | — | READ_FILE |
| · | GET | sellercentral.amazon.in · /marketplace/asin-translation-details | — | READ_FILE |
| · | GET | sellercentral.amazon.in · /multi-channel/listings/api/catalogs | — | READ |

## Response shapes (full field lists, from live capture)

- **`/account-switcher/global-and-regional-account/merchantMarketplace`** (18 fields): `globalAccount`, `globalAccount.delegationContext`, `globalAccount.delegationContextWithTargetPartnerAccount`, `globalAccount.id`, `globalAccount.label`, `globalAccount.searchIds`, `globalAccount.selected`, `parentGlobalAccount`, `regionalAccount`, `regionalAccount.domain`, `regionalAccount.globalAccountId`, `regionalAccount.ids`, `regionalAccount.ids.mons_sel_dir_mcid`, `regionalAccount.ids.mons_sel_mkid`, `regionalAccount.label`, `regionalAccount.searchIds`, `regionalAccount.selected`, `regionalAccount.typeLabel`
- **`/meld/mons-api/GetMarketplaceSwitcher`** (27 fields): `defaultSelection`, `defaultSelection.countryCode`, `defaultSelection.flagCode`, `defaultSelection.marketplaceId`, `defaultSelection.marketplaceName`, `defaultSelection.marketplaceType`, `defaultSelection.merchantId`, `defaultSelection.merchantName`, `defaultSelection.services`, `defaultSelection.services.description`, `defaultSelection.services.id`, `defaultSelection.services.name`, `defaultSelection.services.redirectLink`, `defaultSelection.stack`, `delegationContext`, `homePodStack`, `merchantMarketplaceList`, `merchantMarketplaceList.countryCode`, `merchantMarketplaceList.flagCode`, `merchantMarketplaceList.marketplaceId`, `merchantMarketplaceList.marketplaceName`, `merchantMarketplaceList.marketplaceType`, `merchantMarketplaceList.merchantId`, `merchantMarketplaceList.merchantName`, `merchantMarketplaceList.services`, `merchantMarketplaceList.stack`, `partialResult`

## Out of scope (writes / POST-reads / exports) — never wired into a read-only CLI

| Method | Host · Path | Class | Why held out |
|---|---|---|---|
| ? | sellercentral.amazon.in · /marketplace/set-listing-preferences | WRITE | write-verb constant/path token (G1: deny) |

## UNKNOWN / telemetry (documented, denied per G1)

| Method | Host · Path | Class |
|---|---|---|
| ? | sellercentral.amazon.in · /global-selling/listings/connect | UNKNOWN |
| ? | sellercentral.amazon.in · /marketplace/exchange-rates | UNKNOWN |
| ? | sellercentral.amazon.in · /marketplace/global-listings-expansion-data | UNKNOWN |
| ? | sellercentral.amazon.in · /marketplace/listing-preferences | UNKNOWN |
| ? | sellercentral.amazon.in · /marketplace/recommendation | UNKNOWN |

## Connections

- Index: [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Amazon-Data-Model]]
- Auth & safety: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]

