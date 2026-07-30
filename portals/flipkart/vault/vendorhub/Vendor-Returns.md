---
title: Vendor-Returns
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Returns

> ⚠️ READ-ONLY. Return orders summary and RTV for the 1P vendor lane.

**Endpoints in this section:** 1 — 1 read-safe (READ/READ_FILE), 0 write/export (out of scope), 0 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/return-orders-summary` | fetchApi | READ |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
