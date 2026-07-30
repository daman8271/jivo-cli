---
title: Vendor-Catalog-and-Feeds
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Catalog-and-Feeds

> ⚠️ READ-ONLY. Cataloging (browse-tree, FSN create, feeds) and QC-norms / BIS compliance feeds.

**Endpoints in this section:** 12 — 4 read-safe (READ/READ_FILE), 4 write/export (out of scope), 4 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/browse-tree` | — | READ |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/feed-list` | fetchApi | READ |
| R-file | POST | `vendorhub.flipkart.com/vendor/feeds/download-feed-file` | action | READ_FILE |
| R | UNKNOWN | `vendorhub.flipkart.com/vendor/qc-norms/bis-list` | fetchApi | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/create-fsn` | — | WRITE |
| UNKNOWN | `vendorhub.flipkart.com/vendor/feeds/upload-feed-file` | — | WRITE |
| UNKNOWN | `vendorhub.flipkart.com/vendor/qc-norms/upload-bis-certificates` | — | WRITE |
| UNKNOWN | `vendorhub.flipkart.com/vendor/qc-norms/upload-feed-file` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/check-template` | — |
| UNKNOWN | `vendorhub.flipkart.com/vendor/cataloging/vertical-attributes` | — |
| UNKNOWN | `vendorhub.flipkart.com/vendor/feeds/feed-list` | fetchApi |
| UNKNOWN | `vendorhub.flipkart.com/vendor/feeds/feed-search` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
