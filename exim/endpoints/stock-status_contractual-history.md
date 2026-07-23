---
title: "EXIM endpoint — GET /stock-status/contractual-history/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/contractual-history/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/contractual-history/`

> Contractual history of stock items (rates, contract dates).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/contractual-history/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 68,
    "item_code": "RM000MR",
    "item_name": "MUSTARD REFINED",
    "vendor_code": "VENDA001695",
    "vendor_name": "M/S ARORA AGRI BUSINESS VENTURES",
    "rate": "147.000",
    "contract_start": "2026-05-14",
    "contract_end": "2026-05-21",
    "created_at": "2026-05-20T05:16:00.115864Z",
    "created_by": "raspreet@exim.com"
  },
  {
    "id": 59,
    "item_code": "RM000MR",
    "item_name": "MUSTARD REFINED",
    "vendor_code": "VENDA000224",
    "vendor_name": "AWL AGRI BUSINESS LIMITED",
    "rate": "145.000",
    "contract_start": "2026-05-13",
    "contract_end": "2026-06-14",
    "created_at": "2026-05-19T07:09:01.506014Z",
    "created_by": "raspreet@exim.com"
  },
  "...(+18 more of 20)"
]
```

## Field reference

- `id` — contract-history record id.
- `item_code` / `item_name` — SAP item code and oil name (e.g. `RM000MR`, MUSTARD REFINED).
- `vendor_code` / `vendor_name` — SAP supplier code and name the contract was struck with.
- `rate` — contracted rate as a decimal string (₹ per kg, e.g. "147.000").
- `contract_start` / `contract_end` — contract validity window (ISO dates).
- `created_at` — when the record was entered (ISO datetime, UTC).
- `created_by` — email of the user who logged the contract.

## Used by pages

- [[pages/contractual-history|Contractual History]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]]
- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]]
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]]
- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]]
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]]
- [[endpoints/stock-status_id|`GET /stock-status/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
