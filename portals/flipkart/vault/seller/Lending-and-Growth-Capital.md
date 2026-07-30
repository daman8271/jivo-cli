---
title: Lending-and-Growth-Capital
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Lending-and-Growth-Capital

> ⚠️ READ-ONLY. Seller lending and Flipkart Growth Capital applications.

**Endpoints in this section:** 6 — 0 read-safe (READ/READ_FILE), 3 write/export (out of scope), 3 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/acceptApplication` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/create-lead` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/declineApplication` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/describe-offer` | — |
| UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/es-discovery` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/fkgrowthcapital/getOffers` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
