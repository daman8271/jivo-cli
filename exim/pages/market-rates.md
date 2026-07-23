---
title: Market Rates
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /commodity/market-rates
section: Commodity Price
---

# Market Rates

[[INDEX|JIVO EXIM]] › **Commodity Price** › Market Rates

**Route:** `/commodity/market-rates`  ·  **Web:** `https://exim.jivo.in/commodity/market-rates`

## What this page does

Displays market rates per commodity as maintained in the rates module: each row carries `factory_kg`, `with_packing`, `with_gst_kg` and `with_gst_ltr` for a date. The default view is the latest rate per commodity (`/rates/market-rate/latest/`), and a start/end date range loads historical rows via `/rates/market-rate/get/`. The commodity master (`/rates/commodity/`, ~12 commodities with an optional `margin_rate` like 3.00) resolves commodity ids to names and supplies the margin applied on top of market cost.

## How it helps

Market rates are the cost input from which JIVO's own basic rates are derived (market rate + commodity margin + packing margin). Finance and ops users check this page to verify today's market cost per commodity before rate-setting, and to trace how a rate changed over a period.

## Backend endpoints

- [[endpoints/rates_commodity|`GET /rates/commodity/`]] — Commodity master with margin rates.
- [[endpoints/rates_market-rate_get|`GET /rates/market-rate/get/`]] — Market rate rows over a date range.
- [[endpoints/rates_market-rate_latest|`GET /rates/market-rate/latest/`]] — Latest market rate per commodity.

## Key data & interactions

- Latest-rates table (default): Commodity, Factory ₹/kg, With Packing, With GST/kg, With GST/ltr, Date.
- `start_date` / `end_date` range pickers to load historical market-rate rows for comparison.
- Commodity list with per-commodity Margin Rate (%) from the commodity master (null when no margin is set).

## Related pages (same section)

- [[pages/daily-price|Daily Price]]
- [[pages/jivo-rates|Jivo Rates]]
- [[pages/our-rates|Our Rates]]


Linked: [[INDEX]] · [[API-INVENTORY]]
