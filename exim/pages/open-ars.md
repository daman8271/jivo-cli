---
title: Open ARs
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /accounts/open-ars
section: Accounts
---

# Open ARs

[[INDEX|JIVO EXIM]] › **Accounts** › Open ARs

**Route:** `/accounts/open-ars`  ·  **Web:** `https://exim.jivo.in/accounts/open-ars`

## What this page does

Lists every open accounts-receivable invoice synced from SAP via `GET /sap-sync/open-ar/` (about 1,100 rows). Each row shows Invoice Num, Invoice Date, Invoice Due Date, the customer (Vendor Code/Vendor Name in SAP terms, e.g. `CUSTA000985`), Invoice Total, remaining Balance, and Days Open, plus dispatch context: ShipToCode, Address, Dispatch Date, Bilty Num/Date, Transporter, and Vehicle Number. Comments trace each invoice back to its sales order ("Based On Sales Orders ...").

## How it helps

Finance opens this to work uncollected invoices one by one: Days Open against the due date shows which invoices are overdue, and the bilty/transporter/vehicle columns let ops confirm dispatch actually happened before pressing a customer for payment. It is the document-level companion to the aggregated Customer Outstanding view.

## Backend endpoints

- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]] — Open accounts-receivable documents (SAP).

## Key data & interactions

- Invoice table: Invoice Num, Invoice Date, Invoice Due Date, Vendor Code, Vendor Name (customer), Invoice Total, Balance, Days Open
- Dispatch columns: ShipToCode, Address, Dispatch Date, Bilty Num, Bilty Date, Transporter, Vehicle Number
- Comments column linking each AR to its source sales order
- Search/sort by customer or Days Open; client-side filtering (endpoint takes no query params); INR totals in Cr/Lakh

## Related pages (same section)

- [[pages/exim-account|Oil Dr/Cr Outstanding]]
- [[pages/vendor-outstanding|Vendor Outstanding]]
- [[pages/customer-outstanding|Customer Outstanding]]
- [[pages/customer-aging|Customer Aging]]
- [[pages/open-aps|Open APs]]
- [[pages/open-pos|Open POs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
