---
title: Domestic Contracts (FY 2026-27)
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /contracts/domestic-2627
section: Domestic Contracts
---

# Domestic Contracts (FY 2026-27)

[[INDEX|JIVO EXIM]] › **Domestic Contracts** › Domestic Contracts (FY 2026-27)

**Route:** `/contracts/domestic-2627`  ·  **Web:** `https://exim.jivo.in/contracts/domestic-2627`

## What this page does

Lists all domestic purchase contracts for financial year 2026-27, loaded from `GET /dc/?year=2026`. Each row is a PO for loose oil (e.g. SOYABEAN REFINED LOOSE OIL, MUSTARD LOOSE OIL) with vendor, PO number/date, contract quantity in MTS, rate and total value, then the fulfilment trail as it fills in: load/unload quantities, shortage vs allowed shortage, deductions, transporter and bility details, freight, brokerage, vehicle, invoice, and the GRPO number/date once goods are received. The page also pulls `GET /items/rm/` (23 SAP-synced raw-material items, RM0000001+) and `GET /parties/` (137 SAP business partners) so contracts can be entered or filtered against valid product and vendor codes.

## How it helps

This is where JIVO ops track each current-FY domestic oil purchase from CONTRACT through delivery to GRPO, catching shortages beyond the allowed limit and unbilled deductions before payment. Finance and directors use contract_rate and contract_total (₹3.7 Cr-scale POs) to see committed spend per vendor and per raw material for FY 2026-27.

## Backend endpoints

- [[endpoints/dc|`GET /dc/`]] — Domestic contracts by FY (re-listed).
- [[endpoints/items_rm|`GET /items/rm/`]] — Raw-material item master (SAP-synced).
- [[endpoints/parties|`GET /parties/`]] — Business partners (vendors + customers) master from SAP.

## Key data & interactions

- Contracts table: status, product_name / product_code (RM code), vendor_name / vendor_code, po_number, po_date, contract_qty, contract_rate, contract_total.
- Fulfilment columns per row: load_qty, unload_qty, shortage, allow_shortage, deduction_qty, deduction_amount, basic_amount.
- Logistics columns: transporter_name, bility_number, bility_date, frieght_rate, freight_amount, brokerage_amount, vehicle_number, invoice_number.
- Receipt columns: grpo_number, grpo_date; Completed flag separates closed vs open contracts.
- Filters fed by masters: RM item picker from `/items/rm/` and vendor picker from `/parties/` (card_code / card_name); FY fixed to 2026-27 via `year=2026` on `/dc/`.
- Refresh reloads all three endpoints.

## Related pages (same section)

- [[pages/domestic-contracts|Domestic Contracts (FY 2025-26)]]
- [[pages/open-grpos|Open GRPOs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
