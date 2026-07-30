---
title: Compliance-and-Regulation
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Compliance-and-Regulation

> ⚠️ READ-ONLY. Regulation approvals, audit, approval-store, product compliance.

**Endpoints in this section:** 15 — 10 read-safe (READ/READ_FILE), 1 write/export (out of scope), 4 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/approval-store/latest-status` | — | READ |
| R | GET | `seller.flipkart.com/napi/approval-store/questions` | — | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditDetails` | — | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditMetaData` | — | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditPQDetails` | — | READ |
| R | GET | `seller.flipkart.com/napi/audit/auditPQResults` | — | READ |
| R | GET | `seller.flipkart.com/napi/audit/categoriesFilter` | — | READ |
| R | GET | `seller.flipkart.com/napi/regulation/approvalRequest` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/regulation/approvalStatusWithProcessId` | fetchApi | READ |
| R | GET | `seller.flipkart.com/napi/regulation/auditDetails` | — | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/audit/updateAudit` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/approval-store/requestsV2` | — |
| UNKNOWN | `seller.flipkart.com/napi/approval-store/requestsV2-count` | — |
| UNKNOWN | `seller.flipkart.com/napi/audit/audits` | — |
| UNKNOWN | `seller.flipkart.com/napi/regulation/approvalStatus` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
