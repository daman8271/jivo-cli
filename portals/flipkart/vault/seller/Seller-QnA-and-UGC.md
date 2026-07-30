---
title: Seller-QnA-and-UGC
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Seller-QnA-and-UGC

> ⚠️ READ-ONLY. Product Q&A and seller-generated content answers.

**Endpoints in this section:** 12 — 5 read-safe (READ/READ_FILE), 2 write/export (out of scope), 5 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R-file | GET | `seller.flipkart.com/napi/qnaStore/getDocumentsMetadata` | — | READ_FILE |
| R | GET | `seller.flipkart.com/napi/qnaStore/questions` | — | READ |
| R | GET | `seller.flipkart.com/napi/qnaStore/questionsV2` | — | READ |
| R | GET | `seller.flipkart.com/napi/ugc/fetchSellerAnsweredProductIds` | — | READ |
| R | GET | `seller.flipkart.com/napi/ugc/fetchSellerAnsweredQuestions` | — | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/qnaStore/submit` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/ugc/submitAnswer` | — | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/riddler/fetchSellerQnACount` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/ugc/fetchAllAnswersForQuestion` | — |
| UNKNOWN | `seller.flipkart.com/napi/ugc/fetchAnsweredQuestionsForFSN` | — |
| UNKNOWN | `seller.flipkart.com/napi/ugc/fetchUnansweredQuestionsForFSN` | — |
| UNKNOWN | `seller.flipkart.com/napi/ugc/searchAnsweredQuestions` | — |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
