---
title: Vendor-Users-and-Access
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Users-and-Access

> ⚠️ READ-ONLY. User management, roles & warehouses, UAM authorisation, vendor picker, aggregate entities.

**Endpoints in this section:** 14 — 10 read-safe (READ/READ_FILE), 4 write/export (out of scope), 0 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/aggregate-entities` | updateApi | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/uam/isResourcesAuthorised` | — | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/profile` | — | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/profile/my` | — | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/roles-and-warehouses` | fetchApi | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/user` | — | READ |
| R | GET | `vendorhub.flipkart.com/vendor/user-management/user-data` | fetchApi | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/users/active` | fetchApi | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/users/suspended` | fetchApi | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/vendor-list` | — | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/change-password` | — | WRITE |
| UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/update-user` | — | WRITE |
| UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/user-activation/activate` | — | WRITE |
| UNKNOWN | `vendorhub.flipkart.com/vendor/user-management/user-activation/suspend` | — | WRITE |

## PROVEN detail & live findings (this session)

**PROVEN-READ (GET, 200 live):** `vendor/user-management/vendor-list` (the 6-vendor picker),
`/profile/my`, `/users/active`, `/users/suspended`, `/roles-and-warehouses`, `/aggregate-entities`.

**Who has access to JIVO MART (VEN23097) — VERIFIED live:** **3 active users, 0 suspended**, all
role **Operations Head**:
- abhilash kutty `<abhilashkutty0@gmail.com>` — created 2022-08-29, last_login none
- Gurvinder Jivo `<gurvinder@jivo.in>` — created 2018-11-21, last_login 2019-05-16
- Kalpana Thakur `<kalpana@jivo.in>` — created 2023-07-07, last_login none

(Interactive logins are near-dormant — JIVO drives this account via API automation, not the GUI.)

**Roles catalogue (portal-wide):** `V_OH` Operations Head, `V_FRM` Flipkart Relationship Manager,
and more, each with an entity→actions permission map (FINANCE:VIEW, PRODUCT_COMPLIANCE:VIEW/MODIFY,
INVENTORY_PRODUCTS:VIEW, PAYMENT:VIEW, AGREEMENTS_APP:VIEW/MODIFY, MANAGE_USERS…).
**Warehouses / vendor sites (2):** `VS58039` West Delhi 110027, `VS96323011` Bengaluru Rural 562123.

**The 6 vendors for gurvinder@jivo.in (VERIFIED live):** VEN23097 JIVO MART · VEN19086 CHIRAG
ENTERPRISES · VEN20606 FAIRDEAL MARKETING · VEN19640 M/S SHIV SHAKTI ENTERPRISES · VEN21197
KNOWTABLE ONLINE SERVICES · VEN18904 Jivo wellness private limited. (+ infinite@jivo.in's 3:
VEN20104 BABA LOKENATH, VEN54675 SUSTAINQUEST, Evara Enterprises — token expired, documented.)

**To pull the other 8 entities' data (PENDING_AUTH):** the read endpoints are scoped by the session's
*selected* vendor. Switching is `POST /select-vendor` (a WRITE — this study will not author it). The
sanctioned path: let the app/keepalive select each vendor, then run the read-only CLI's
`vendor purchase-orders` / analytics reads once per vendor.

**Out of scope (writes):** `user-activation/activate`, `/suspend`, `change-password`, `update-user`,
`/select-vendor` — catalogued, never fired.

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
