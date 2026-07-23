---
title: Customer Aging
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /accounts/customer-aging
section: Accounts
---

# Customer Aging

[[INDEX|JIVO EXIM]] › **Accounts** › Customer Aging

**Route:** `/accounts/customer-aging`  ·  **Web:** `https://exim.jivo.in/accounts/customer-aging`

## What this page does

Invoice-level aging of customer receivables from `GET /sap-sync/customer-aging-balance/` (about 4,850 open invoice rows synced from SAP). Each row carries DocNum, DocDate, Days_Difference and a ready-made Aging bucket label ("0-30 Days" etc.), plus CardCode/CardName, salesperson (SlpName), ShipToCode, DocTotal, PaidToDate, the invoice Balance, and the customer's total Outstanding Amount. The page groups these into aging buckets per customer so old unpaid invoices stand out from current billing.

## How it helps

This is the collections prioritization view: finance sees exactly which invoices sit in the older buckets and how much of each customer's balance is overdue vs current. SlpName and ShipToCode let a director route follow-up to the right salesperson and delivery location instead of chasing a lump-sum balance.

## Backend endpoints

- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]] — Customer aging balances (SAP).

## Key data & interactions

- Aging-bucket grouping driven by the Aging field ("0-30 Days", older buckets) and Days_Difference
- Invoice columns: DocNum, DocDate, CardCode, CardName, SlpName, ShipToCode, DocTotal, PaidToDate, Balance, customer Outstanding Amount
- Filter/search by customer, salesperson, or bucket; all client-side (endpoint takes no query params)
- INR amounts shown in Cr/Lakh; per-bucket and per-customer subtotals

## Related pages (same section)

- [[pages/exim-account|Oil Dr/Cr Outstanding]]
- [[pages/vendor-outstanding|Vendor Outstanding]]
- [[pages/customer-outstanding|Customer Outstanding]]
- [[pages/open-ars|Open ARs]]
- [[pages/open-aps|Open APs]]
- [[pages/open-pos|Open POs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
