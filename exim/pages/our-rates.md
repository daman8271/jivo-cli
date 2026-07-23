---
title: Our Rates
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /commodity/our-rates
section: Commodity Price
---

# Our Rates

[[INDEX|JIVO EXIM]] › **Commodity Price** › Our Rates

**Route:** `/commodity/our-rates`  ·  **Web:** `https://exim.jivo.in/commodity/our-rates`

## What this page does

Shows JIVO's own computed selling rates (basic rates) derived from market rates plus commodity and packing margins. The headline view is the composite latest rate table (`/rates/rate-table/latest/`): a pack-size x commodity grid, e.g. "Pouch 1 Ltr" priced across Soya Refined 145.87, Ricebran Refined 149.49, Mustard Refined 166.08. Underneath, `/rates/basic-rate/` returns dated rows with `basic_price_kg` and `basic_price_ltr` linked to a `packing_type` and `market_rate`, while `/rates/commodity/` (margin_rate per commodity), `/rates/packing/` (Pouch 10%, Tin 14% packing margins) and the market-rate endpoints supply the inputs the basic price is built from over a start/end range.

## How it helps

This page answers "what should we sell at today, per pack size and commodity" with the margin math already applied, so sales can quote from one grid instead of recomputing market cost + margins. Directors use the market-vs-basic comparison over a date range to check that margins are holding as commodity costs move.

## Backend endpoints

- [[endpoints/rates_basic-rate|`GET /rates/basic-rate/`]] — Basic (our) rate rows over a date range.
- [[endpoints/rates_commodity|`GET /rates/commodity/`]] — Commodity master with margin rates.
- [[endpoints/rates_market-rate_get|`GET /rates/market-rate/get/`]] — Market rate rows over a date range.
- [[endpoints/rates_market-rate_latest|`GET /rates/market-rate/latest/`]] — Latest market rate per commodity.
- [[endpoints/rates_packing|`GET /rates/packing/`]] — Packing types with packing margins.
- [[endpoints/rates_rate-table_latest|`GET /rates/rate-table/latest/`]] — Composite latest rate table (commodities + rows).

## Key data & interactions

- Latest rate-table grid: rows = pack sizes (Pouch 1 Ltr, Pouch 750 Gm, ...), columns = commodities (Soya Refined, Cottonseed Refined, Ricebran Refined, Mustard Refined), cells = basic price.
- `start_date` / `end_date` range pickers loading dated basic-rate rows (Basic ₹/kg, Basic ₹/ltr, packing type, linked market rate).
- Market-rate reference table (latest per commodity: factory ₹/kg, with packing, with GST/kg, with GST/ltr) for side-by-side comparison.
- Margin inputs on display: commodity `margin_rate` (%) and packing margins per packing type (Pouch 10.00, Tin 14.00).

## Related pages (same section)

- [[pages/daily-price|Daily Price]]
- [[pages/jivo-rates|Jivo Rates]]
- [[pages/market-rates|Market Rates]]


Linked: [[INDEX]] · [[API-INVENTORY]]
