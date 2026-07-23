---
title: "EXIM endpoint — GET /sap-sync/customer/balance/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/customer/balance/
category: sap-sync
kind: read
resource: customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/customer/balance/`

> Customer outstanding balance over a date range (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/customer/balance/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `startDate`, `endDate` |

## Response — real sample (trimmed)

```json
{
  "data": [
    {
      "Balance": 24288042.97
    }
  ]
}
```

## Field reference

- `data[]` — one-row array holding the aggregate balance result.
- `data[].Balance` — customer net outstanding balance across the `startDate`–`endDate` range (₹). Positive means the customer owes JIVO.

## Notes

- Read-only GET. Ported from the sibling build (`daman8271/exim`) to close a coverage gap.
- CLI: `exim <group> get-...`. Part of [[API-INVENTORY]] · [[INDEX]]

Linked: [[API-INVENTORY]] · [[INDEX]]
