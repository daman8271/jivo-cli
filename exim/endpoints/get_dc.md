---
title: "EXIM endpoint — GET /dc/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /dc/
category: dc
kind: read
resource: domesticcontracts
auth: bearer
---

# `GET /dc/`

> Domestic contracts by FY (re-listed).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/dc/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `year` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 304,
    "product_name": "SOYABEAN REFINED LOOSE OIL",
    "vendor_name": "AWL AGRI BUSINESS LIMITED",
    "status": "CONTRACT",
    "product_code": "RM0000025",
    "vendor_code": "VENDA000224",
    "po_number": "220526051",
    "po_date": "2026-05-13",
    "contract_qty": "250.00",
    "contract_rate": "149500.00",
    "contract_total": "37375000.00",
    "load_qty": null,
    "basic_amount": null,
    "unload_qty": null,
    "shortage": null,
    "allow_shortage": null,
    "deduction_qty": null,
    "deduction_amount": null,
    "transporter_code": null,
    "transporter_name": null,
    "bility_number": null,
    "bility_date": null,
    "frieght_rate": null,
    "freight_amount": null,
    "grpo_date": null,
    "grpo_number": null,
    "brokerage_amount": null,
    "vehicle_number": null,
    "invoice_number": null,
    "created_by": "",
    "created_at": "2026-05-14T07:01:03.588019Z",
    "deleted": 0,
    "Completed": 0
  },
  {
    "id": 307,
    "product_name": "MUSTARD LOOSE OIL",
    "vendor_name": "AWL AGRI BUSINESS LIMITED",
    "status": "CONTRACT",
    "product_code": "RM0000003",
    "vendor_code": "VENDA000224",
    "po_number": "220526066",
    "po_date": "2026-05-13",
    "contract_qty": "250.00",
    "contract_rate": "149500.00",
    "contract_total": "37375000.00",
    "load_qty": null,
    "basic_amount": null,
    "unload_qty": null,
    "shortage": null,
    "allow_shortage": null,
    "deduction_qty": null,
    "deduction_amount": null,
    "transporter_code": null,
    "transporter_name": null,
    "bility_number": null,
    "bility_date": null,
    "frieght_rate": null,
    "freight_amount": null,
    "grpo_date": null,
    "grpo_number": null,
    "brokerage_amount": null,
    "vehicle_number": null,
    "invoice_number": null,
    "created_by": "",
    "created_at": "2026-05-19T08:16:01.134274Z",
    "deleted": 0,
    "Completed": 0
  },
  "...(+45 more of 47)"
]
```

## Field reference

- `id` — domestic-contract record ID.
- `product_name` / `product_code` — oil being bought and its SAP raw-material code (e.g. MUSTARD LOOSE OIL, `RM0000003`).
- `vendor_name` / `vendor_code` — supplier and its SAP business-partner code.
- `status` — lifecycle stage; `CONTRACT` = booked, downstream freight/loading fields still null.
- `po_number` / `po_date` — SAP purchase-order number and date (ISO date).
- `contract_qty` — contracted quantity in MTS.
- `contract_rate` — agreed rate in ₹ per MT.
- `contract_total` — contract value in ₹ (qty x rate).
- `load_qty` / `unload_qty` — MTS loaded vs received; `shortage` and `allow_shortage` compare the two, `deduction_qty` / `deduction_amount` charge back excess shortage (MTS / ₹).
- `basic_amount` — ₹ value of loaded quantity at contract rate.
- `transporter_code` / `transporter_name`, `bility_number` / `bility_date`, `frieght_rate` / `freight_amount`, `vehicle_number` — freight-stage carrier, bilty (lorry receipt), freight ₹ and truck (API typo "frieght").
- `grpo_number` / `grpo_date` — SAP Goods Receipt PO reference on receipt.
- `brokerage_amount` / `invoice_number` — broker commission ₹ and vendor invoice.
- `created_by` / `created_at` — audit trail (ISO 8601 UTC timestamp).
- `deleted` / `Completed` — soft-delete flag and contract-closed flag (0/1).

## Used by pages

- [[pages/domestic-2627|Domestic Contracts (FY 2026-27)]]

## Related endpoints

- [[endpoints/dc|`GET /dc/`]]
- [[endpoints/dc_dropdown|`GET /dc/dropdown/`]]
- [[endpoints/dc_contract_create|`POST /dc/contract/create/`]]
- [[endpoints/dc_freight_create_id|`POST /dc/freight/create/{id}/`]]
- [[endpoints/dc_loading_create_id|`POST /dc/loading/create/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `domesticcontracts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
