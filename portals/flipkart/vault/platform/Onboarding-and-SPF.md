---
title: Onboarding-and-SPF
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, platform, read-only]
status: studied
---

# Onboarding-and-SPF

> ⚠️ READ-ONLY. Seller onboarding, SPF, partner services.

**Endpoints in this section:** 6 — 1 read-safe (READ/READ_FILE), 3 write/export (out of scope), 2 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/onboarding/getBranchByIFSC` | fetchApi | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/onboarding/generateOtpMobile` | checkNumberExistence | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/onboarding/updateBookSellerBusinessDetails` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/onboarding/updateSellerBankDetailsV3` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/onboarding/fetchAllBankDetails` | — |
| UNKNOWN | `seller.flipkart.com/napi/onboarding/taskDetailsFirefly` | fetchApi |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
