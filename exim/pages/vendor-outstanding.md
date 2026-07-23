---
title: Vendor Outstanding
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /accounts/vendor-outstanding
section: Accounts
---

# Vendor Outstanding

[[INDEX|JIVO EXIM]] › **Accounts** › Vendor Outstanding

**Route:** `/accounts/vendor-outstanding`  ·  **Web:** `https://exim.jivo.in/accounts/vendor-outstanding`

## What this page does

Shows the SAP-synced vendor outstanding balance sheet from `GET /sap-sync/vendor/balance-sheet/` (about 387 VENDA vendor accounts, including inter-company parties like JIVO WELLNESS PVT LTD - HR/DL). Each row lists CardCode, CardName, the net Balance (negative = amount JIVO owes the vendor), and the Last Transaction Date and Last Transaction Amount on that account.

## How it helps

Finance uses it to size total payables exposure and decide which vendors to pay next; large balances with old Last Transaction Dates flag accounts that need reconciliation or settlement. It is the vendor-side mirror of Customer Outstanding and the aggregate view behind the document-level Open APs page.

## Backend endpoints

- [[endpoints/sap-sync_vendor_balance-sheet|`GET /sap-sync/vendor/balance-sheet/`]] — Vendor outstanding balance sheet (SAP).
- [[endpoints/sap_sync_vendor_ledger|`GET /sap-sync/vendor/ledger/`]] — Vendor ledger entries for one party (SAP).

## Key data & interactions

- Vendor table: CardCode, CardName, Balance (signed, INR), Last Transaction Date, Last Transaction Amount
- Sort by balance to rank the largest payables; amounts shown in Cr/Lakh
- Client-side search over the ~387 vendor rows (endpoint takes no query params)
- Refresh re-pulls the SAP vendor balance-sheet sync

## Related pages (same section)

- [[pages/exim-account|Oil Dr/Cr Outstanding]]
- [[pages/customer-outstanding|Customer Outstanding]]
- [[pages/customer-aging|Customer Aging]]
- [[pages/open-ars|Open ARs]]
- [[pages/open-aps|Open APs]]
- [[pages/open-pos|Open POs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
