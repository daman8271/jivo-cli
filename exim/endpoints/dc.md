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

> Domestic contracts (delivery challans / POs) for a given financial year.

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
- `product_name` / `product_code` — oil being bought and its SAP raw-material code (e.g. SOYABEAN REFINED LOOSE OIL, `RM0000025`).
- `vendor_name` / `vendor_code` — supplier and its SAP business-partner code (e.g. `VENDA000224`).
- `status` — lifecycle stage; `CONTRACT` = booked, freight/loading fields still null until later stages fill them.
- `po_number` / `po_date` — SAP purchase-order number and its date (ISO date).
- `contract_qty` — contracted quantity in MTS (e.g. "250.00").
- `contract_rate` — agreed rate in ₹ per MT (e.g. 149500.00).
- `contract_total` — contract value in ₹ (`contract_qty` x `contract_rate`, e.g. ₹3.74 Cr).
- `load_qty` / `unload_qty` — MTS loaded at vendor vs received at unload; null until loading happens.
- `basic_amount` — ₹ value of the loaded quantity at contract rate.
- `shortage` / `allow_shortage` — transit shortage in MTS vs allowed tolerance.
- `deduction_qty` / `deduction_amount` — shortage beyond tolerance charged back (MTS / ₹).
- `transporter_code` / `transporter_name` — carrier assigned at freight stage.
- `bility_number` / `bility_date` — bilty (lorry receipt) number and date.
- `frieght_rate` / `freight_amount` — freight rate and total freight ₹ (note API typo "frieght").
- `grpo_number` / `grpo_date` — SAP Goods Receipt PO reference once material is received.
- `brokerage_amount` — broker commission in ₹, if any.
- `vehicle_number` / `invoice_number` — truck registration and vendor invoice.
- `created_by` / `created_at` — who created the record and when (ISO 8601 UTC).
- `deleted` — soft-delete flag (0/1).
- `Completed` — 1 when the contract is fully closed, else 0.

## Used by pages

- [[pages/domestic-2627|Domestic Contracts (FY 2026-27)]]
- [[pages/domestic-contracts|Domestic Contracts (FY 2025-26)]]

## Related endpoints

- [[endpoints/get_dc|`GET /dc/`]]
- [[endpoints/dc_dropdown|`GET /dc/dropdown/`]]
- [[endpoints/dc_contract_create|`POST /dc/contract/create/`]]
- [[endpoints/dc_freight_create_id|`POST /dc/freight/create/{id}/`]]
- [[endpoints/dc_loading_create_id|`POST /dc/loading/create/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `domesticcontracts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
