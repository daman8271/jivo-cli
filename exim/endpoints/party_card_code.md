---
title: "EXIM endpoint — GET /party/{card_code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /party/{card_code}/
category: party
kind: detail
resource: party
auth: bearer
---

# `GET /party/{card_code}/`

> Single business-partner detail.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/party/{card_code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `card_code` |

## Response — real sample (trimmed)

```json
{
  "id": 11,
  "card_code": "VENDA000102",
  "card_name": "A. L. BADA ENGINEERING",
  "state": "GJ",
  "u_main_group": "EXPORT",
  "country": "IN"
}
```

## Field reference

- `id` — internal EXIM database id.
- `card_code` — SAP business-partner card code (path parameter echoed back; `VEND…` prefix for vendors).
- `card_name` — party legal name (e.g. `A. L. BADA ENGINEERING`).
- `state` — Indian state code (`GJ` = Gujarat).
- `country` — ISO country code (`IN`).
- `u_main_group` — SAP main-group user-field classifying the relationship (`EXPORT`, `PURCHASE OIL`, …).

## Used by pages

- [[pages/stock-status|Stock Status]]

## Related endpoints

- [[endpoints/delete_party_card_code|`DELETE /party/{card_code}/`]]

## Notes

- Kind: **detail**. Resource permission group: `party`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
