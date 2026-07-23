---
title: "EXIM endpoint — GET /parties/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /parties/
category: parties
kind: read
resource: party
auth: bearer
---

# `GET /parties/`

> Business partners (vendors + customers) master from SAP.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/parties/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "count": 137,
  "parties": [
    {
      "id": 11,
      "card_code": "VENDA000102",
      "card_name": "A. L. BADA ENGINEERING",
      "state": "GJ",
      "u_main_group": "EXPORT",
      "country": "IN"
    },
    {
      "id": 12,
      "card_code": "VENDA000161",
      "card_name": "AASHIRWAD OIL & AGRO INDUSTRIES",
      "state": "HR",
      "u_main_group": "PURCHASE OIL",
      "country": "IN"
    },
    "...(+135 more of 137)"
  ]
}
```

## Field reference

- `count` — number of parties in the master (137 in sample).
- `parties[]` — one entry per SAP-synced business partner:
  - `id` — internal EXIM database id.
  - `card_code` — SAP business-partner card code (e.g. `VENDA000102`, `VEND…` prefix for vendors).
  - `card_name` — party legal name (e.g. `A. L. BADA ENGINEERING`).
  - `state` — Indian state code (`GJ` = Gujarat, `HR` = Haryana).
  - `country` — ISO country code (`IN`).
  - `u_main_group` — SAP main-group user-field classifying the relationship (`EXPORT`, `PURCHASE OIL`, …); used to filter parties per module.

## Used by pages

- [[pages/domestic-2627|Domestic Contracts (FY 2026-27)]]
- [[pages/stock-status|Stock Status]]
- [[pages/sync-vendor-data|Sync Vendor Data]]

## Related endpoints

- _(none)_

## Notes

- Kind: **read**. Resource permission group: `party`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
