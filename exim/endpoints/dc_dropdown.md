---
title: "EXIM endpoint — GET /dc/dropdown/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /dc/dropdown/
category: dc
kind: read
resource: domesticcontracts
auth: bearer
---

# `GET /dc/dropdown/`

> Open-PO dropdown for domestic-contract creation.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/dc/dropdown/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 307,
    "po_number": "220526066",
    "vendor_code": "VENDA000224",
    "vendor_name": "AWL AGRI BUSINESS LIMITED",
    "product_code": "RM0000003",
    "product_name": "MUSTARD LOOSE OIL"
  },
  {
    "id": 306,
    "po_number": "220526038",
    "vendor_code": "VENDA000614",
    "vendor_name": "DHANLAXMI EDIBLES PRIVATE LIMITED",
    "product_code": "RM0000011",
    "product_name": "GROUNDNUT LOOSE OIL"
  },
  "...(+199 more of 201)"
]
```

## Field reference

- `id` — internal ID of the open purchase order; passed back when creating a domestic contract against it.
- `po_number` — SAP purchase-order number (e.g. `220526066`) shown as the dropdown label.
- `vendor_code` — SAP business-partner code of the supplier (e.g. `VENDA000224`).
- `vendor_name` — supplier legal name (e.g. AWL AGRI BUSINESS LIMITED).
- `product_code` — SAP raw-material item code (e.g. `RM0000003`, `RM` = raw material).
- `product_name` — oil product on the PO (e.g. MUSTARD LOOSE OIL).

## Used by pages

- [[pages/domestic-contracts|Domestic Contracts (FY 2025-26)]]

## Related endpoints

- [[endpoints/dc|`GET /dc/`]]
- [[endpoints/get_dc|`GET /dc/`]]
- [[endpoints/dc_contract_create|`POST /dc/contract/create/`]]
- [[endpoints/dc_freight_create_id|`POST /dc/freight/create/{id}/`]]
- [[endpoints/dc_loading_create_id|`POST /dc/loading/create/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `domesticcontracts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
