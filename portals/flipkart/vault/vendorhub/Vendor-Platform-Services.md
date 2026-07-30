---
title: Vendor-Platform-Services
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, vendorhub, read-only]
status: studied
---

# Vendor-Platform-Services

> ⚠️ READ-ONLY. Retail-palantir request bus, Ryuk document jobs, Triton feed processor — the plumbing under the SPA.

**Endpoints in this section:** 8 — 1 read-safe (READ/READ_FILE), 2 write/export (out of scope), 5 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `vendorhub.flipkart.com/retail-palantir/v1/request` | url | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/ryuk/v1/document/bulk_upload_template/client_reference_id/` | — | WRITE |
| POST | `vendorhub.flipkart.com/triton/v1/feed/processor/upload` | url | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `vendorhub.flipkart.com/api/` | — |
| UNKNOWN | `vendorhub.flipkart.com/ryuk/v1/document/retail_fulfilment_asn_action_history/client_reference_id/` | — |
| UNKNOWN | `vendorhub.flipkart.com/ryuk/v1/document/retail_fulfilment_report/client_reference_id/` | — |
| UNKNOWN | `vendorhub.flipkart.com/triton/v1/feed/clientRefId/` | — |
| POST | `vendorhub.flipkart.com/triton/v1/feed/search` | url |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
