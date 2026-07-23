---
title: "EXIM endpoint — GET /daily-price/fetch/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /daily-price/fetch/
category: daily-price
kind: sync
resource: dailyprice/daily_price
auth: bearer
---

# `GET /daily-price/fetch/`

> Fetch/refresh the latest daily commodity prices; returns status + preview. [RECLASSIFIED: pull-and-store / sync-trigger — writes data, excluded from read CLI]

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/daily-price/fetch/` |
| Auth | `Authorization: Bearer <access_token>` |

## ⚠️ MUTATION — excluded from the read-only CLI

Despite being an HTTP `GET`, this endpoint **writes data**: it pulls fresh data from the upstream source (SAP / rate feed) and **upserts it into EXIM's database**. Evidence:
- Permission grants only `fetch`/`sync` (not `view`).
- Response is an import result (`status`/`count`/`preview_data` or `Items_processed`), not plain data.
- Lives in the `/sap_sync/` (underscore) sync namespace, or is a `*/fetch/` refresh action.

The app fires these on page load to refresh; the CLI does **not** expose them, so tooling can never trigger a write. Documented here for completeness only.

## Related
- [[API-INVENTORY]] · [[HARD-RULE]] · [[INDEX]]

Linked: [[API-INVENTORY]] · [[INDEX]]
