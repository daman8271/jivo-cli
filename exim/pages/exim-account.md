---
title: Oil Dr/Cr Outstanding
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /exim-account
section: Accounts
---

# Oil Dr/Cr Outstanding

[[INDEX|JIVO EXIM]] › **Accounts** › Oil Dr/Cr Outstanding

**Route:** `/exim-account`  ·  **Web:** `https://exim.jivo.in/exim-account`

## What this page does

Shows the Oil Dr/Cr outstanding balance sheet from `GET /sap-sync/balance-sheet/` — a compact SAP-synced list (about 23 party accounts, mostly VENDA vendor codes like `VENDA001347` INDRANI FOODS) with each party's net Balance plus its Last Transaction Date and Last Transaction Amount. Negative balances are credits owed to the party; the same endpoint also feeds the Dashboard.

## How it helps

Gives directors a one-screen Dr/Cr position on the oil-trade party accounts: who JIVO owes, who owes JIVO, and whether an account has gone stale (Last Transaction Date months back with a large balance still open). It supports payment-release and settlement decisions without opening SAP.

## Backend endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]] — Oil Dr/Cr outstanding balance sheet (SAP).

## Key data & interactions

- Party table: CardCode, CardName, Balance (INR, signed Dr/Cr), Last Transaction Date, Last Transaction Amount
- Sort by balance to surface the largest debit/credit exposures; amounts formatted in Cr/Lakh
- Client-side search over party name/code (endpoint takes no query params)
- Refresh re-pulls the SAP balance-sheet sync

## Related pages (same section)

- [[pages/vendor-outstanding|Vendor Outstanding]]
- [[pages/customer-outstanding|Customer Outstanding]]
- [[pages/customer-aging|Customer Aging]]
- [[pages/open-ars|Open ARs]]
- [[pages/open-aps|Open APs]]
- [[pages/open-pos|Open POs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
