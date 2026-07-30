---
title: Accounts And Entities
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, platform, platform]
status: studied
---


# Accounts And Entities

> The three JIVO accounts and what each may see.

The account surface is what makes multi-entity coverage possible.
`instamart/v1/account/list` returns the full entity graph and
`api/v1/account/permissions` returns the signed-in user's domains.

Live, `ecom1@jivo.in` (user id **345**) can select **three** accounts, and the
`/account-select` screen states it plainly: *"Welcome ecom1, You can access both
the Brand and Supply portal from below."*

| Account (selectable) | Account id | brandCompany id | brandAccount id |
|---|---|---|---|
| **Jivo Mart Pvt. Ltd** | `89bafc9c-8a56-4286-94cf-a55ab4e564d3` | `935ac57d898d4c1b3b8ec0001a87d28a44b12928` | `e4d59d18-4a2a-4ccb-a03c-2bbdb4474b79` |
| **Jivo Wellness** | `c9f24655-a984-4b65-a4da-2d5b6461b9ec` | `5ecb3c0025f73c6716097e1a1a6e62390ceb2504` | `260921c1-76e7-48ef-9771-82124ebe1fcc` |
| **Jivo** (brand under Wellness) | `260921c1-76e7-48ef-9771-82124ebe1fcc` | — | brand `1bd421f677aba0b28ef95a6ed80970824cdf83ec` |

Permissions returned `userType: USER_TYPE_BRAND`, `personas: []`, and
`accessibleDomains: ["DOMAIN_ADS", "DOMAIN_CATALOG", "DOMAIN_PARTNER"]`.

**Endpoints in this section:** 4 (4 read, 0 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | GET | `brand-portal-service-http.swiggy.com/api/v1/account/permissions` | `ACCOUNT_PERMISSIONS` | **PROVEN LIVE 200** | call site .get() on ACCOUNT_PERMISSIONS | live: ['POST'] -> [200], 481B |
| READ | GET | `partner-api.swiggy.com/instamart/v1/account/get` | `ACCOUNT_GET` | **PROVEN LIVE 200** | call site .get() on ACCOUNT_GET | live: ['GET'] -> [200], 619B |
| READ | GET | `partner-api.swiggy.com/instamart/v1/account/list` | `ACCOUNT_LIST` | **PROVEN LIVE 200** | call site .get() on ACCOUNT_LIST | live: ['GET'] -> [200], 1464B |
| READ | GET | `partner-api.swiggy.com/instamart/v1/account/permissions` | `ACCOUNT_PERMISSIONS` | documented (not observed live) | call site .get() on ACCOUNT_PERMISSIONS |

### Out of scope (writes / exports) — never exposed in a read-only CLI

_None in this section._

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- **A naming error in JIVO's own automation.** `~/.config/swiggy-instamart-cli/
  config.json` maps `brand_accounts.mart -> c9f24655...`, but the live
  `/account-select` tile for `c9f24655...` is **Jivo Wellness**, and Jivo Mart is
  `89bafc9c...`. VERIFIED by clicking each tile and reading back
  `__IM_ADS_CURRENT_ACCOUNT_ID__`. The consequence — whether the daily sales
  upload is labelling Mart and Wellness data correctly — is **INFERRED and worth
  a human check**; this study did not trace the upload.
- The hierarchy is `brandCompany -> account -> brandAccount -> brand`. Several
  internal notes use "brand id" for three different levels of it.
- Every account object returned `status: "ACCOUNT_STATE_INVALID"` and an empty
  `name` — a Swiggy-side data quirk, not an account problem; the display names
  come from `brandCompany.name`.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-02-account-select.png`

  ![screenshot](../captures/walk1/sec-02-account-select.png)
- `sec-01-account-select.png`

  ![screenshot](../captures/walk2/sec-01-account-select.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
