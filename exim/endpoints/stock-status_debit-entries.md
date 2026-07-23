---
title: "EXIM endpoint — GET /stock-status/debit-entries/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/debit-entries/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/debit-entries/`

> Shortage/debit deduction entries per vehicle/item.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/debit-entries/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 14,
    "item_code": "RM00C01",
    "item_name": "CANOLA",
    "rate": "132000.000",
    "load_qty": "41.490",
    "unload_qty": "41.390",
    "shortage_qty": "0.100",
    "allowed_shortage_qty": "0.104",
    "deducted_shortage_qty": "0.000",
    "deduction_amount": "0.000",
    "supplier_code": "VENDA001035",
    "supplier": "ALBA EDIBLE OILS PTY LTD",
    "vehicle_number": "RJ47GA6771",
    "transporter": "RK TANKER SERVICE",
    "bility_number": null,
    "grpo_number": null,
    "created_at": "2026-04-25T13:09:27.557362Z",
    "created_by": "raspreet@exim.com",
    "stock": 355
  },
  {
    "id": 15,
    "item_code": "RM00C01",
    "item_name": "CANOLA",
    "rate": "125000.000",
    "load_qty": "41.700",
    "unload_qty": "41.670",
    "shortage_qty": "0.030",
    "allowed_shortage_qty": "0.104",
    "deducted_shortage_qty": "0.000",
    "deduction_amount": "0.000",
    "supplier_code": "VENDA000599",
    "supplier": "EDIBLE OIL CO D LLC",
    "vehicle_number": "RJ47GA8215",
    "transporter": null,
    "bility_number": null,
    "grpo_number": null,
    "created_at": "2026-04-27T14:02:36.750500Z",
    "created_by": "raspreet@exim.com",
    "stock": 347
  },
  "...(+128 more of 130)"
]
```

## Field reference

- `id` — debit-entry id.
- `item_code` / `item_name` — SAP item code and oil name (e.g. `RM00C01`, CANOLA).
- `rate` — rate used to value the shortage (₹ per MTS, e.g. "132000.000").
- `load_qty` — quantity loaded at origin (MTS).
- `unload_qty` — quantity received at unloading (MTS).
- `shortage_qty` — load minus unload (MTS).
- `allowed_shortage_qty` — transit-loss tolerance for this load (MTS); shortage within it is not charged.
- `deducted_shortage_qty` — shortage beyond tolerance actually charged to the supplier (MTS).
- `deduction_amount` — money debited for that excess shortage (₹ = deducted_shortage_qty × rate).
- `supplier_code` / `supplier` — SAP vendor code and name.
- `vehicle_number` / `transporter` — truck registration and transport company.
- `bility_number` / `grpo_number` — bilty (lorry receipt) and SAP Goods Receipt PO numbers, nullable.
- `created_at` / `created_by` — entry timestamp (ISO datetime, UTC) and creator email.
- `stock` — id of the linked stock-status row (`GET /stock-status/{id}/`).

## Used by pages

- [[pages/shortage-report|Shortage Report]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
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
