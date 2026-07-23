---
title: Stock Status
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/stock-status
section: Stock
---

# Stock Status

[[INDEX|JIVO EXIM]] › **Stock** › Stock Status

**Route:** `/stock/stock-status`  ·  **Web:** `https://exim.jivo.in/stock/stock-status`

## What this page does

The working ledger of every import stock row from `GET /stock-status/`: item (e.g. RM0MKG MUSTARD KACHI GHANI), vendor, rate and rate_in_litres, quantity and quantity_in_litre, lifecycle status (IN_CONTRACT through COMPLETED), payment_status, contract_start/contract_end, vehicle_number, transporter and location. Rows can be filtered by the `status` query param, new rows created via `POST /stock-status/`, and the KPI header comes from `GET /stock-status/stock-insights/` (total_value, total_qty_kg/litre, avg_price_per_kg/ltr, total_count). Vendor and item pickers are fed by `GET /parties/` (SAP partner master) and `GET /tank/items/`.

## How it helps

This is the single answer to "how much oil do we own, where is it, and what did it cost" - roughly ₹122 Cr of stock across ~222 rows in the sample data. Ops uses it to track each consignment through the IN_CONTRACT -> ON_THE_SEA -> ... -> COMPLETED pipeline; finance uses avg price per kg/litre and payment_status to plan payouts against contract windows.

## Backend endpoints

- [[endpoints/parties|`GET /parties/`]] — Business partners (vendors + customers) master from SAP.
- [[endpoints/stock-status|`GET /stock-status/`]] — Create a stock-status record.
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]] — Aggregate stock KPIs (value, qty, avg price).
- [[endpoints/stock-status_stock-summary|`GET /stock-status/stock-summary/`]] — Aggregate stock summary KPIs (value, qty, avg price).
- [[endpoints/tank_items|`GET /tank/items/`]] — Tank item master (code, name, category, colour).

## Key data & interactions

- Status filter (`?status=`) across the 8 lifecycle statuses, plus item-code and vendor filters fed by `/tank/items/` and `/parties/`
- KPI cards from stock-insights: total value (₹ Cr), total qty in KG and LITERS, avg price per KG / per LTR, record count
- Row columns: item_code/name, vendor, status, rate + rate_in_litres, quantity + quantity_in_litre, contract_start/end, ETA, arrival_date, vehicle_number, transporter, location, payment_status, bility/GRPO numbers
- KG / MTS / LITERS unit toggle on quantity columns
- Add-stock form (POST /stock-status/) with vendor dropdown from the SAP parties master

## Related pages (same section)

- [[pages/shortage-report|Shortage Report]]
- [[pages/contractual-history|Contractual History]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-monitoring|Tank Monitoring]]
- [[pages/tank-data|Tank Data]]
- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/tank-logs|Tank Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
