---
title: Ads AI Chat
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, ads, ads]
status: studied
---


# Ads AI Chat

> An in-portal AI assistant over JIVO's own ads data.

The shell ships an **AI chat assistant** — chunks `AskMeAnything` and
`AiChatPanel` — backed by `ads-chat/chat` plus conversation list, history and
delete endpoints. It answers questions over the account's own ads data inside the
portal.

Nobody at JIVO appears to know it exists, and the config flag
`AI_ASSISTANT_FULL_ROLLOUT` is **false**, so it is gated off for this account
even though the client code and endpoints ship.

**Endpoints in this section:** 4 (2 read, 1 write/export, 1 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/conversations/list` | `ADS_CHAT_LIST_SESSIONS` | documented (not observed live) | call site .post() on ADS_CHAT_LIST_SESSIONS |
| READ | POST | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/conversations/{conversation_id}/messages/list` | `ADS_CHAT_GET_SESSION` | documented (not observed live) | call site .post() on ADS_CHAT_GET_SESSION |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| DELETE | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/conversations/{conversation_id}` | `ADS_CHAT_DELETE_SESSION` | WRITE — call site .delete() on ADS_CHAT_DELETE_SESSION |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

| METHOD | Host · Path | Const | Why it stays denied |
|---|---|---|---|
| POST | `brand-portal-service-http.swiggy.com/api/v1/ads-chat/chat` | `ADS_CHAT` | call site .post() on ADS_CHAT |

## Gotchas

- `ads-chat/chat` posts a prompt and creates a conversation record; classified
  UNKNOWN and **not** exercised (G1). Sending a prompt would write a
  conversation row.
- `conversations/{conversation_id}` on **DELETE** removes a session — excluded.
- The listing endpoints (`conversations/list`,
  `conversations/{id}/messages/list`) are reads.

## Screenshots (live read-only walk, 2026-07-30)

_No screenshot is attributed to this section; its endpoints are exercised from pages captured under sibling notes. See [[Swiggy-Instamart-Screenshot-Index]] for the full set._

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
