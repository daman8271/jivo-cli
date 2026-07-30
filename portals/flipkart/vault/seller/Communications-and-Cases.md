---
title: Communications-and-Cases
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, seller, read-only]
status: studied
---

# Communications-and-Cases

> ⚠️ READ-ONLY. Seller-buyer communications (SBC), case manager, notifications.

**Endpoints in this section:** 40 — 3 read-safe (READ/READ_FILE), 13 write/export (out of scope), 24 UNKNOWN (denied per G1, documented).

All contracts are reverse-read from the on-disk SPA JS corpus (`captures/js/*`) unless a row is marked PROVEN in the notes. Method is taken from the bundle where resolvable, else `?`. Auth per [[Auth-and-Access]].

## Read-safe endpoints (allowlist)

| R/W | METHOD | Host · Path | Const | Class |
|---|---|---|---|---|
| R | GET | `seller.flipkart.com/napi/get-notifications` | — | READ |
| R | GET | `seller.flipkart.com/napi/get-notifications-count` | fetchApi | READ |
| R | UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getChatKey` | fetchApi | READ |

## Out of scope — writes/exports (never expose in a read-only CLI)

| METHOD | Host · Path | Const | Class |
|---|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/case-manager/getCreateTicketForm` | — | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/spf-claims` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/submitIssue` | customURL | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/submitReply` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/mark-all-notifications` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/notifications/update` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/createConversation` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/createSirIncidents` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/isSellerEnabled` | fetchApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/proposeCancellation` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/updateActor` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/updateActorState` | updateApi | WRITE |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/updateConversation` | updateApi | WRITE |

## UNKNOWN — method/posture unresolved (G1: denied, documented only)

| METHOD | Host · Path | Const |
|---|---|---|
| UNKNOWN | `seller.flipkart.com/napi/case-manager/general-tickets` | — |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/getSellerDetails` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/issue-schema` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/issue-seller-close` | — |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/issue-thread` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/issues-search` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/case-manager/sub-issue-types` | — |
| UNKNOWN | `seller.flipkart.com/napi/notifications/action` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/chatMeta` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/existingBuyer` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getActorState` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getBuyerList` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getChatMessageCount` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getChatMessages` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getConversationList` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getEvents` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getLatestEvents` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getListingForSeller` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getMetricsData` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/getPageBuyerList` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/postChatMessages` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/searchReturnId` | fetchApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/sellerHeartBeat` | updateApi |
| UNKNOWN | `seller.flipkart.com/napi/sellerBuyerCommunications/sirCounts` | fetchAPI |

## Connections

- Index: [[Flipkart-Endpoints]] · Routes: [[Flipkart-Pages-and-Routes]] · Data model: [[Flipkart-Data-Model]] · Auth: [[Auth-and-Access]] · Guardrails: [[Read-Only-Guardrails]] · Atlas: [[00-Flipkart-Atlas]]
