---
title: Domestic Contracts (FY 2025-26)
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /domestic-contracts
section: Domestic Contracts
---

# Domestic Contracts (FY 2025-26)

[[INDEX|JIVO EXIM]] › **Domestic Contracts** › Domestic Contracts (FY 2025-26)

**Route:** `/domestic-contracts`  ·  **Web:** `https://exim.jivo.in/domestic-contracts`

## What this page does

Shows the FY 2025-26 domestic contract register from `GET /dc/` filtered to the prior financial year via the `year` param. Each contract row carries product and vendor (with RM product_code and vendor_code), PO number and date, contract_qty / contract_rate / contract_total, and the full delivery record: load and unload quantities, shortage against allow_shortage, deductions, transporter, bility number/date, freight and brokerage amounts, vehicle, invoice, and GRPO number/date. The Completed flag marks contracts fully received and closed.

## How it helps

The FY 2025-26 archive lets finance reconcile last year's domestic oil purchases: what was contracted vs actually unloaded, what shortages and deductions were applied, and which invoices and GRPOs closed each PO. Directors reference it for year-over-year vendor rates and volumes against the current FY 2026-27 page.

## Backend endpoints

- [[endpoints/dc|`GET /dc/`]] — Domestic contracts by FY (re-listed).

## Key data & interactions

- Contract columns: status, product_name, product_code, vendor_name, vendor_code, po_number, po_date, contract_qty, contract_rate, contract_total.
- Delivery columns: load_qty, unload_qty, shortage, allow_shortage, deduction_qty, deduction_amount, basic_amount.
- Logistics and billing columns: transporter_name, bility_number, bility_date, frieght_rate, freight_amount, brokerage_amount, vehicle_number, invoice_number, grpo_number, grpo_date.
- Completed flag distinguishes closed contracts from open ones.
- Single data source: `GET /dc/` with `year` pinned to FY 2025-26; Refresh re-fetches the list.

## Related pages (same section)

- [[pages/domestic-2627|Domestic Contracts (FY 2026-27)]]
- [[pages/open-grpos|Open GRPOs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
