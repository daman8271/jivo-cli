---
title: "EXIM endpoint — GET /sap-sync/open-ap/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/open-ap/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/open-ap/`

> Open accounts-payable documents (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/open-ap/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "Open APs": [
    {
      "DB Primary Key": 48250,
      "Invoice Number": 626074168,
      "Status (O=Open C=Closed)": "O",
      "Invoice Date": "2026-07-14T00:00:00",
      "Payment Due Date": "2026-07-14T00:00:00",
      "Tax Posting Date": "2026-07-11T00:00:00",
      "Vendor Code": "VENDA000930",
      "Vendor Name": "VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED",
      "Vendor GST Number": null,
      "Vendor Invoice Reference No": "VARPL/2627/01871",
      "Total Invoice Amount (INR)": 6052234.0,
      "Total Invoice Amount (Foreign Currency)": 0.0,
      "GST / VAT Amount": 288476.4,
      "Discount Amount": 0.0,
      "Amount Paid So Far": 0.0,
      "Reference 1": "626074168",
      "Remarks / Notes": "Based On Purchase Orders 220726046. GATE ENTRY NO 156 Based On Goods Receipt PO 2026076618.",
      "Journal Entry Memo": "A/P Invoices - VENDA000930",
      "Journal Entry Number": 220471,
      "Bilty / LR Number": "8560",
      "Bilty / LR Date": "2026-07-11T00:00:00",
      "Transporter Name": "R.K. TANKER SERVICE",
      "Vehicle Number": "RJ47GA7520",
      "Goods Received Date": null,
      "Linked GRN Doc Entry": null,
      "GRN Vendor Code": null,
      "GRN Warehouse Code": null
    },
    {
      "DB Primary Key": 48253,
      "Invoice Number": 626074170,
      "Status (O=Open C=Closed)": "O",
      "Invoice Date": "2026-07-13T00:00:00",
      "Payment Due Date": "2026-07-13T00:00:00",
      "Tax Posting Date": "2026-07-09T00:00:00",
      "Vendor Code": "VENDA000224",
      "Vendor Name": "AWL AGRI BUSINESS LIMITED",
      "Vendor GST Number": null,
      "Vendor Invoice Reference No": "190826018334",
      "Total Invoice Amount (INR)": 6229109.0,
      "Total Invoice Amount (Foreign Currency)": 0.0,
      "GST / VAT Amount": 296907.0,
      "Discount Amount": 0.0,
      "Amount Paid So Far": 0.0,
      "Reference 1": "626074170",
      "Remarks / Notes": "MUSTARD Based On Purchase Orders 220526066. gate entry  no 140 Based On Goods Receipt PO 2026076616.",
      "Journal Entry Memo": "A/P Invoices - VENDA000224",
      "Journal Entry Number": 220475,
      "Bilty / LR Number": "155",
      "Bilty / LR Date": "2026-07-09T00:00:00",
      "Transporter Name": "HEM TRANSPORT",
      "Vehicle Number": "GJ39TB1829",
      "Goods Received Date": null,
      "Linked GRN Doc Entry": null,
      "GRN Vendor Code": null,
      "GRN Warehouse Code": null
    },
    "...(+157 more of 159)"
  ]
}
```

## Field reference

- `Open APs[]` — one row per open A/P (purchase) invoice, 159 in the sample.
- `DB Primary Key` — SAP internal DocEntry of the invoice row.
- `Invoice Number` — A/P invoice document number.
- `Status (O=Open C=Closed)` — invoice status flag; endpoint returns `O` rows.
- `Invoice Date` / `Payment Due Date` / `Tax Posting Date` — document, due, and tax-posting dates (ISO datetime).
- `Vendor Code` / `Vendor Name` / `Vendor GST Number` — SAP vendor identity; GSTIN may be null.
- `Vendor Invoice Reference No` — vendor's own invoice number.
- `Total Invoice Amount (INR)` — gross invoice value in ₹; `Total Invoice Amount (Foreign Currency)` — same in the document currency when an import invoice (0.0 for domestic).
- `GST / VAT Amount` — tax component of the invoice (₹).
- `Discount Amount` — discount applied (₹).
- `Amount Paid So Far` — payments already applied (₹); open balance = total minus this.
- `Reference 1` — SAP reference field (mirrors the invoice number here).
- `Remarks / Notes` — free text linking base documents (PO number, gate entry, GRPO number).
- `Journal Entry Memo` / `Journal Entry Number` — posted journal-entry description and number.
- `Bilty / LR Number`, `Bilty / LR Date`, `Transporter Name`, `Vehicle Number` — inbound transport (lorry receipt) details.
- `Goods Received Date`, `Linked GRN Doc Entry`, `GRN Vendor Code`, `GRN Warehouse Code` — linkage to the goods-receipt (GRN/GRPO) document; null when not linked.

## Used by pages

- [[pages/open-aps|Open APs]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]
- [[endpoints/sap-sync_open-pos|`GET /sap-sync/open-pos/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
