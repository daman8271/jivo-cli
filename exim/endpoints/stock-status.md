---
title: "EXIM endpoint — GET /stock-status/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/`

> Core import stock-status rows (optionally filtered by status).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `status` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 542,
    "item_code": "RM0MKG",
    "item_name": "MUSTARD KACHI GHANI",
    "vendor_code": "VENDA000224",
    "vendor_name": "AWL AGRI BUSINESS LIMITED",
    "eta": null,
    "status": "IN_CONTRACT",
    "rate": "165.000",
    "quantity": "250000.00",
    "total": "0.00",
    "rate_in_litres": "150.150",
    "quantity_in_litre": "274725.00",
    "job_work": null,
    "vehicle_number": null,
    "transporter": null,
    "location": "BUNDI, RAJASTHAN",
    "is_accumulator": false,
    "arrival_date": null,
    "remainder_action": null,
    "bility_number": null,
    "grpo_number": null,
    "payment_status": "UNPAID",
    "contract_start": "2026-06-12",
    "contract_end": "2026-07-12",
    "created_at": "2026-06-13T05:36:35.057986Z",
    "created_by": "raspreet@exim.com",
    "deleted": false,
    "parent": null
  },
  {
    "id": 598,
    "item_code": "RM00SB",
    "item_name": "SOYABEAN",
    "vendor_code": "VENDA000224",
    "vendor_name": "AWL AGRI BUSINESS LIMITED",
    "eta": null,
    "status": "IN_CONTRACT",
    "rate": "147.500",
    "quantity": "132020.00",
    "total": "0.00",
    "rate_in_litres": "134.225",
    "quantity_in_litre": "145076.78",
    "job_work": null,
    "vehicle_number": null,
    "transporter": null,
    "location": "GUJARAT",
    "is_accumulator": false,
    "arrival_date": null,
    "remainder_action": null,
    "bility_number": null,
    "grpo_number": null,
    "payment_status": "UNPAID",
    "contract_start": "2026-06-26",
    "contract_end": "2026-07-26",
    "created_at": "2026-06-27T08:23:03.897938Z",
    "created_by": "lovepreet@exim.com",
    "deleted": false,
    "parent": null
  },
  "...(+7 more of 9)"
]
```

## Field reference

- `id` — stock-status row id (used by `GET /stock-status/{id}/` and referenced as `stock` in logs/debit entries).
- `item_code` / `item_name` — EXIM stock/tank-grade code and oil name (e.g. `RM0MKG`, MUSTARD KACHI GHANI). A live 2026-07-19 profile found 0/27 exact overlap between these grade codes and the 23-code SAP RM master (`RM0000003`-style), so this field must not be treated as a SAP item key without a reviewed, effective-dated mapping.
- `vendor_code` / `vendor_name` — SAP supplier code and name.
- `eta` — expected arrival date (ISO date, nullable).
- `status` — lifecycle status (IN_CONTRACT → ON_THE_SEA → MUNDRA_PORT → ON_THE_WAY → UNDER_LOADING → AT_REFINERY → OUT_SIDE_FACTORY → COMPLETED); also the `status` query filter.
- `rate` — contracted rate per kg (₹, decimal string, e.g. "165.000").
- `quantity` — quantity in kg (decimal string; "250000.00" = 250 MTS).
- `total` — total value (₹; "0.00" while still in contract).
- `rate_in_litres` / `quantity_in_litre` — same rate and quantity converted to litres (kg → litre via oil density, e.g. 250000 kg = 274725 L).
- `job_work` — job-work reference if out for third-party processing, else `null`.
- `vehicle_number` / `transporter` — truck registration and transport company once dispatched, else `null`.
- `location` — current/source location of the stock (e.g. "BUNDI, RAJASTHAN").
- `is_accumulator` — flag marking an accumulator row that aggregates child records.
- `arrival_date` — actual arrival date (ISO date, nullable).
- `remainder_action` — pending follow-up action noted on the row, else `null`.
- `bility_number` — bilty (lorry receipt) number, nullable.
- `grpo_number` — SAP Goods Receipt PO number once received, nullable.
- `payment_status` — supplier payment state (e.g. `UNPAID`).
- `contract_start` / `contract_end` — contract validity window (ISO dates).
- `created_at` / `created_by` — record creation timestamp (ISO datetime, UTC) and creator email.
- `deleted` — soft-delete flag.
- `parent` — parent stock row id when this row was split from another, else `null`.

## Used by pages

- [[pages/contracts|Contracts]]
- [[pages/dashboard|Dashboard]]
- [[pages/stock-status|Stock Status]]
- [[pages/vehicle-report|Vehicle Report]]

## Related endpoints

- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
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
