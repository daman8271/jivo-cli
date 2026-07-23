---
title: "EXIM endpoint — GET /stock-status/stock-summary/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/stock-summary/
category: stock-status
kind: read
resource: stockstatus
auth: bearer
---

# `GET /stock-status/stock-summary/`

> Aggregate stock summary KPIs (value, qty, avg price).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/stock-summary/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |

## Response — real sample (trimmed)

```json
// (empty)
```

## Field reference

- Sample captured empty, so no field shapes are confirmed. Per the endpoint description it returns aggregate stock-summary KPIs: total stock value (₹), total stock quantity (MTS), and average price (₹ per MTS).

## Notes

- Read-only GET. Ported from the sibling build (`daman8271/exim`) to close a coverage gap.
- CLI: `exim <group> get-...`. Part of [[API-INVENTORY]] · [[INDEX]]

Linked: [[API-INVENTORY]] · [[INDEX]]
