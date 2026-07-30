---
title: GraphQL-Data-Core
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, platform, read-only]
status: studied
---

# GraphQL-Data-Core

> ⚠️ READ-ONLY. The single /napi/graphql gateway — every dashboard widget is a GraphQL operation.

**Endpoints in this section:** 2 — 1 read-safe (READ/READ_FILE), 0 write/export (out of scope), 1 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `seller.flipkart.com/napi/graphql` | fetchApi | READ |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/graphql-sse` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
