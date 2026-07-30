---
title: Vendor-Documents
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Documents

> ⚠️ READ-ONLY. Document service: getFile/getDocument downloads, static documents, upload templates.

**Endpoints in this section:** 5 — 2 read-safe (READ/READ_FILE), 2 write/export (out of scope), 1 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R-file | UNKNOWN | `vendorhub.flipkart.com/vendor-p/download-file/` | href | READ_FILE |
| R-file | UNKNOWN | `vendorhub.flipkart.com/vendor-p/getFile/v1/retail/documents/` | — | READ_FILE |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor-p/document-service/v1/retail/documents/upload` | url | WRITE |
| UNKNOWN | `vendorhub.flipkart.com/vendor-p/upload/legal-metrology/feed/upload` | url | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor-portal/home` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
