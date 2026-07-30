---
title: Promotions
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Promotions

> ⚠️ READ-ONLY. Flipkart promotion / offer participation surfaces.

**Endpoints in this section:** 6 — 0 read-safe (READ/READ_FILE), 3 write/export (out of scope), 3 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/myp/create-promotion` | createApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/myp/enable-disable-promotion` | enableDisableApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerPromotions/uploaded-listings-status` | fileUploadStatus | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/myp/get-promotion` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/myp/get-promotions` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/promotions/check-flo-seller` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
