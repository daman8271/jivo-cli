---
title: Open APs
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /accounts/open-aps
section: Accounts
---

# Open APs

[[INDEX|JIVO EXIM]] › **Accounts** › Open APs

**Route:** `/accounts/open-aps`  ·  **Web:** `https://exim.jivo.in/accounts/open-aps`

## What this page does

Lists open accounts-payable invoices synced from SAP via `GET /sap-sync/open-ap/`. Each row is a vendor invoice (Invoice Number, Invoice Date, Payment Due Date, Tax Posting Date, Status O/C) against a vendor like `VENDA000930` VAISHNODEVI AGRO, with Total Invoice Amount (INR and foreign currency), GST/VAT Amount, Discount, and Amount Paid So Far. Rows also carry procurement and logistics trace fields: Vendor Invoice Reference No, Journal Entry Number/Memo, Bilty/LR Number and Date, Transporter Name, Vehicle Number, and links back to the purchase order and Goods Receipt PO in the remarks.

## How it helps

Finance uses it to plan vendor payments: Payment Due Date vs Amount Paid So Far shows what is due and unpaid per vendor, while the GRN/bilty/vehicle trail lets ops verify goods were actually received before an invoice is released for payment.

## Backend endpoints

- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]] — Open accounts-payable documents (SAP).

## Key data & interactions

- Invoice table: Invoice Number, Status (O/C), Invoice Date, Payment Due Date, Tax Posting Date, Vendor Code, Vendor Name, Vendor Invoice Reference No
- Amount columns: Total Invoice Amount (INR), Foreign Currency amount, GST/VAT Amount, Discount Amount, Amount Paid So Far
- Logistics/trace columns: Bilty/LR Number and Date, Transporter Name, Vehicle Number, Journal Entry Number, Remarks with linked PO and Goods Receipt PO numbers
- Search/sort by vendor or due date; client-side filtering (endpoint takes no query params); INR in Cr/Lakh

## Related pages (same section)

- [[pages/exim-account|Oil Dr/Cr Outstanding]]
- [[pages/vendor-outstanding|Vendor Outstanding]]
- [[pages/customer-outstanding|Customer Outstanding]]
- [[pages/customer-aging|Customer Aging]]
- [[pages/open-ars|Open ARs]]
- [[pages/open-pos|Open POs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
