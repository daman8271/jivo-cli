---
title: "EXIM endpoint — GET /stock-status/{id}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/{id}/
category: stock-status
kind: detail
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/{id}/`

> Single stock-status record detail.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/{id}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `id` |

## Response — real sample (trimmed)

```json
{
  "id": 342,
  "item_code": "RM0EL",
  "item_name": "EXTRA LIGHT",
  "vendor_code": "VENDA000004",
  "vendor_name": "JIVO WELLNESS PVT LTD - DL",
  "eta": null,
  "status": "IN_TANK",
  "rate": "567.087",
  "quantity": "32578.03",
  "total": "0.00",
  "rate_in_litres": "516.050",
  "quantity_in_litre": "35800.00",
  "job_work": null,
  "vehicle_number": null,
  "transporter": null,
  "location": "Sonipat Factory",
  "is_accumulator": false,
  "arrival_date": null,
  "remainder_action": null,
  "bility_number": null,
  "grpo_number": null,
  "payment_status": "UNPAID",
  "contract_start": null,
  "contract_end": null,
  "created_at": "2026-04-23T07:35:34.354770Z",
  "created_by": "",
  "deleted": false,
  "parent": null
}
```

## Field reference

- `id` — stock-status row id (the `{id}` path param).
- `item_code` / `item_name` — SAP item code and oil name (e.g. `RM0EL`, EXTRA LIGHT).
- `vendor_code` / `vendor_name` — SAP supplier code and name.
- `eta` — expected arrival date (ISO date, nullable).
- `status` — lifecycle status; besides the main chain (IN_CONTRACT … COMPLETED), values like `IN_TANK` appear for stock sitting in factory tanks.
- `rate` — rate per kg (₹, decimal string, e.g. "567.087").
- `quantity` — quantity in kg (decimal string).
- `total` — total value (₹).
- `rate_in_litres` / `quantity_in_litre` — rate and quantity converted to litres (kg → litre via oil density).
- `job_work` — job-work reference if out for third-party processing, else `null`.
- `vehicle_number` / `transporter` — truck registration and transport company once dispatched, else `null`.
- `location` — current location of the stock (e.g. "Sonipat Factory").
- `is_accumulator` — flag marking an accumulator row that aggregates child records.
- `arrival_date` — actual arrival date (ISO date, nullable).
- `remainder_action` — pending follow-up action noted on the row, else `null`.
- `bility_number` / `grpo_number` — bilty (lorry receipt) and SAP Goods Receipt PO numbers, nullable.
- `payment_status` — supplier payment state (e.g. `UNPAID`).
- `contract_start` / `contract_end` — contract validity window (ISO dates, nullable).
- `created_at` / `created_by` — creation timestamp (ISO datetime, UTC) and creator email (empty for system-created rows).
- `deleted` — soft-delete flag.
- `parent` — parent stock row id when this row was split from another, else `null`.

## Used by pages

- [[pages/stock-status|Stock Status]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]]
- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]]
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]]
- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]]
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]]

## Notes

- Kind: **detail**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
