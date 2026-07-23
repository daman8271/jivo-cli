---
title: Shortage Report
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/variance
section: Stock
---

# Shortage Report

[[INDEX|JIVO EXIM]] › **Stock** › Shortage Report

**Route:** `/stock/variance`  ·  **Web:** `https://exim.jivo.in/stock/variance`

## What this page does

Transit-shortage tracking per vehicle load. `GET /stock-status/debit-entries/` lists each delivery with item, rate, supplier, vehicle_number, transporter, load_qty vs unload_qty, the resulting shortage_qty, the allowed_shortage_qty tolerance, and any deducted_shortage_qty with its deduction_amount in ₹, linked to the source stock row. `GET /stock-status/debit-insights/` supplies the header totals: total_records (130 in sample), total deducted shortage (4.574) and total_deduction_amount (₹7.12 lakh).

## How it helps

It decides whether JIVO gets money back from a supplier or transporter: when unload_qty falls short of load_qty beyond the allowed tolerance, the excess becomes a debit note (deduction_amount). Finance uses the aggregate insights to size total transit-loss recovery; ops uses per-vehicle rows to spot transporters with repeat shortages.

## Backend endpoints

- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]] — Shortage/debit deduction entries per vehicle/item.
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]] — Aggregate shortage/debit totals.

## Key data & interactions

- KPI cards: total records, total deducted shortage qty, total deduction amount (₹)
- Table columns: item_code/name, rate, load_qty, unload_qty, shortage_qty, allowed_shortage_qty, deducted_shortage_qty, deduction_amount, supplier, vehicle_number, transporter, bility/GRPO numbers, created_at
- Filter by supplier, vehicle, transporter; rows over tolerance stand out (deduction_amount > 0)

## Related pages (same section)

- [[pages/stock-status|Stock Status]]
- [[pages/contractual-history|Contractual History]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-monitoring|Tank Monitoring]]
- [[pages/tank-data|Tank Data]]
- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/tank-logs|Tank Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
