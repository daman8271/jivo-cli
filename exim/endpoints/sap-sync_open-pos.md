---
title: "EXIM endpoint — GET /sap-sync/open-pos/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/open-pos/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/open-pos/`

> Open purchase orders (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/open-pos/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "open_pos": [
    {
      "PO_NUMBER": 220426102,
      "PO_DATE": "2026-04-24T00:00:00",
      "DUE_DATE": "2026-04-24T00:00:00",
      "VENDOR_CODE": "VENDA000224",
      "VENDOR_NAME": "AWL AGRI BUSINESS LIMITED",
      "ItemCode": "RM0000003",
      "UserSign": 15,
      "ITEM_NAME": "MUSTARD LOOSE OIL",
      "ORDERED_QTY": 250.0,
      "PENDING_QTY": 49.405,
      "RECEIVED_QTY": 200.595,
      "UNIT_PRICE": 148000.0,
      "OPEN_VALUE": 7311940.0,
      "WAREHOUSE": "BH-GJ",
      "UOM": "MTS"
    },
    {
      "PO_NUMBER": 220526013,
      "PO_DATE": "2026-05-06T00:00:00",
      "DUE_DATE": "2026-05-06T00:00:00",
      "VENDOR_CODE": "VENDA000149",
      "VENDOR_NAME": "MIGASA ACEITES S L U",
      "ItemCode": "RM0000013",
      "UserSign": 15,
      "ITEM_NAME": "POMACE OLIVE LOOSE OIL IMPORTED",
      "ORDERED_QTY": 22.0,
      "PENDING_QTY": 22.0,
      "RECEIVED_QTY": 0.0,
      "UNIT_PRICE": 2050.0,
      "OPEN_VALUE": 45100.0,
      "WAREHOUSE": "BH-GJ",
      "UOM": "MTS"
    },
    "...(+16 more of 18)"
  ]
}
```

## Field reference

- `open_pos[]` — one row per open purchase-order line (18 in the sample).
- `PO_NUMBER` — SAP purchase order number.
- `PO_DATE` / `DUE_DATE` — order date and delivery due date (ISO datetime).
- `VENDOR_CODE` / `VENDOR_NAME` — SAP vendor code (VENDA-prefixed) and name.
- `ItemCode` / `ITEM_NAME` — raw-material item code (RM-prefixed) and description (e.g. MUSTARD LOOSE OIL).
- `UserSign` — SAP user ID that raised the PO.
- `ORDERED_QTY` — quantity ordered, in `UOM` units (MTS in the sample).
- `RECEIVED_QTY` — quantity already received against the line.
- `PENDING_QTY` — quantity still to arrive = ordered minus received.
- `UNIT_PRICE` — price per unit of `UOM` (₹; e.g. ₹148,000/MT for mustard loose oil).
- `OPEN_VALUE` — value of the pending quantity (₹) ≈ `PENDING_QTY` × `UNIT_PRICE`.
- `WAREHOUSE` — destination warehouse code (e.g. `BH-GJ`).
- `UOM` — unit of measure for the quantity fields (`MTS` = metric tonnes).

## Used by pages

- [[pages/open-pos|Open POs]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
