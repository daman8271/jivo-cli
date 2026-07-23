---
title: Customer Outstanding
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /accounts/customer-outstanding
section: Accounts
---

# Customer Outstanding

[[INDEX|JIVO EXIM]] › **Accounts** › Customer Outstanding

**Route:** `/accounts/customer-outstanding`  ·  **Web:** `https://exim.jivo.in/accounts/customer-outstanding`

## What this page does

Shows the SAP-synced outstanding balance sheet for CUSTA customer accounts (about 350 rows) via `GET /sap-sync/custa/balance-sheet/`. Each row is one customer (CardCode like `CUSTA001101`, CardName) with its Outstanding Amount, Outstanding After 1-Apr-26 (current-FY portion), the assigned salesperson (SlpName), and the latest invoice (DocNum, InvoiceDate, InvoiceAmount, Since_Last_Invoice days) alongside the last payment received (Transaction_Date, Transaction_Amount, Since_Last_Transaction days). Amounts are INR; negative Outstanding Amount means the customer holds a credit balance.

## How it helps

Finance and directors use it to chase receivables: Since_Last_Invoice and Since_Last_Transaction expose customers who have gone silent (e.g. 140+ days since last invoice with no payment), and SlpName pins each balance to the salesperson responsible for collection. The After-1-Apr split separates fresh dues from carried-forward old balances.

## Backend endpoints

- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]] — Customer (custa) outstanding balance sheet (SAP).
- [[endpoints/sap_sync_customer_balance|`GET /sap-sync/customer/balance/`]] — Customer outstanding balance over a date range (SAP).
- [[endpoints/sap_sync_customer_ledger|`GET /sap-sync/customer/ledger/`]] — Customer ledger entries for one party (SAP).

## Key data & interactions

- Customer table: CardCode, CardName, SlpName (salesperson), Outstanding Amount, Outstanding After 1-Apr-26, last invoice (DocNum, InvoiceDate, InvoiceAmount, Since_Last_Invoice days), last payment (Transaction_Date, Transaction_Amount, Since_Last_Transaction days)
- Search / sort on customer name and outstanding amount; INR values shown in Cr/Lakh
- Endpoint takes no query params, so all filtering is client-side over the full ~352-row sync
- Refresh pulls a fresh SAP sync of the balance sheet

## Related pages (same section)

- [[pages/exim-account|Oil Dr/Cr Outstanding]]
- [[pages/vendor-outstanding|Vendor Outstanding]]
- [[pages/customer-aging|Customer Aging]]
- [[pages/open-ars|Open ARs]]
- [[pages/open-aps|Open APs]]
- [[pages/open-pos|Open POs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
