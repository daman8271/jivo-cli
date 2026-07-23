---
title: Dashboard
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /dashboard
section: Reports
---

# Dashboard

[[INDEX|JIVO EXIM]] › **Reports** › Dashboard

**Route:** `/dashboard`  ·  **Web:** `https://exim.jivo.in/dashboard`

## What this page does

Landing dashboard combining four feeds: a daily-price trend chart from `GET /daily-price/trends/` (start_date/end_date range, one dataset per RM item such as Soya DO, Soya Refined), the SAP oil Dr/Cr outstanding balance sheet from `GET /sap-sync/balance-sheet/` (party-wise Balance, last transaction date and amount), current stock rows from `GET /stock-status/`, and overall tank utilisation from `GET /tank/capacity-insights/` (filled vs empty capacity and percentages). One screen shows prices, party balances, pipeline stock, and tank headroom together.

## How it helps

The daily situational check: are RM prices moving, which vendors hold large outstanding balances (₹ Cr scale, e.g. -5.06 Cr with INDRANI FOODS), and is there tank capacity for incoming loads. It supports buy/hold price decisions and payment prioritisation without opening SAP.

## Backend endpoints

- [[endpoints/daily-price_trends|`GET /daily-price/trends/`]] — Daily-price trend series (labels + datasets) for charting over a range.
- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]] — Oil Dr/Cr outstanding balance sheet (SAP).
- [[endpoints/stock-status|`GET /stock-status/`]] — Create a stock-status record.
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]] — Overall tank capacity fill/empty percentages.

## Key data & interactions

- Price trend line chart: one series per item (Soya DO, Soya Refined, ~12 datasets), driven by a start_date / end_date date-range picker
- Tank capacity gauge/KPI cards: total_capacity, filled_capacity, filled_percentage (e.g. 66.04%), empty_capacity, empty_percentage
- Balance-sheet table: CardCode, CardName, Balance (INR, shown in Cr/Lakh), Last Transaction Date, Last Transaction Amount
- Stock-status list with per-status quantities; KG / MTS / LITERS unit toggle; Refresh

## Related pages (same section)

- [[pages/stock-dashboard|Stock Dashboard]]
- [[pages/director-dashboard|Director Dashboard]]
- [[pages/warehouse-inventory|Warehouse Inventory]]
- [[pages/vehicle-report|Vehicle Report]]
- [[pages/contracts|Contracts]]
- [[pages/planning|Planning]]


Linked: [[INDEX]] · [[API-INVENTORY]]
