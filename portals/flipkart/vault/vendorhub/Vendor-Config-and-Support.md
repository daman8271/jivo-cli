---
title: Vendor-Config-and-Support
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Config-and-Support

> ⚠️ READ-ONLY. Sale config, ticket portal (Freshworks), support mail, recon tool, TaaS migration check.

**Endpoints in this section:** 5 — 2 read-safe (READ/READ_FILE), 1 write/export (out of scope), 2 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/config/sale-config` | — | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/ticketPortalUrl` | fetchApi | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor/support/send-mail` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor/config` | — |
| UNKNOWN | `vendorhub.flipkart.com/vendor/recon-tool/redirect` | fetchApi |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
