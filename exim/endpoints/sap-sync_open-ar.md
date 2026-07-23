---
title: "EXIM endpoint — GET /sap-sync/open-ar/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/open-ar/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/open-ar/`

> Open accounts-receivable documents (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/open-ar/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "Open ARs": [
    {
      "Invoice Num": 626078203,
      "Invoice Date": "2026-07-18T00:00:00",
      "Invoice Due Date": "2026-07-18T00:00:00",
      "Vendor Code": "ORGC000001",
      "Vendor Name": "GAGANDEEP SINGH",
      "Invoice Total": 25000.0,
      "Balance": 25000.0,
      "Days Open": 0,
      "Comments": "Based On Sales Orders 1726078225.",
      "Address": "NEW DELHI-110027\rIN",
      "Address2": "NEW DELHI-110027\rIN",
      "ShipToCode": "GAGANDEEP SINGH NEW DELHI",
      "Dispatch Date": null,
      "Bilty Num": null,
      "Bilty Date": null,
      "Transporter": null,
      "Vehicle Number": null
    },
    {
      "Invoice Num": 626078202,
      "Invoice Date": "2026-07-18T00:00:00",
      "Invoice Due Date": "2026-07-18T00:00:00",
      "Vendor Code": "CUSTA000985",
      "Vendor Name": "GURU KIRPA AGENCY",
      "Invoice Total": 37500.0,
      "Balance": 37500.0,
      "Days Open": 0,
      "Comments": "Based On Sales Orders 1726078224.",
      "Address": "SABJI MANDI  7713 CLOCK TOWER\rDELHI-110007\rIN",
      "Address2": "SABJI MANDI  7713 CLOCK TOWER\rDELHI-110007\rIN",
      "ShipToCode": "GURU KIRPA AGENCY DELHI",
      "Dispatch Date": null,
      "Bilty Num": null,
      "Bilty Date": null,
      "Transporter": null,
      "Vehicle Number": null
    },
    "...(+1110 more of 1112)"
  ]
}
```

## Field reference

- `Open ARs[]` — one row per open A/R (sales) invoice, 1,112 in the sample.
- `Invoice Num` — A/R invoice document number.
- `Invoice Date` / `Invoice Due Date` — invoice and payment-due dates (ISO datetime).
- `Vendor Code` / `Vendor Name` — the customer's SAP business-partner code and name (labelled "Vendor" by the SAP view; codes are CUSTA/ORGC-prefixed customers).
- `Invoice Total` — gross invoice value (₹).
- `Balance` — unpaid amount still open on the invoice (₹).
- `Days Open` — days since invoice date.
- `Comments` — free text linking the base sales order (e.g. "Based On Sales Orders ...").
- `Address` / `Address2` — bill-to and ship-to addresses (CR-separated lines).
- `ShipToCode` — ship-to address code on the invoice.
- `Dispatch Date`, `Bilty Num`, `Bilty Date`, `Transporter`, `Vehicle Number` — outbound dispatch/lorry-receipt details; null until goods are dispatched.

## Used by pages

- [[pages/open-ars|Open ARs]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-pos|`GET /sap-sync/open-pos/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
