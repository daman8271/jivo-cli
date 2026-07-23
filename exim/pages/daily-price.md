---
title: Daily Price
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /commodity/daily-price
section: Commodity Price
---

# Daily Price

[[INDEX|JIVO EXIM]] › **Commodity Price** › Daily Price

**Route:** `/commodity/daily-price`  ·  **Web:** `https://exim.jivo.in/commodity/daily-price`

## What this page does

Shows the daily factory price sheet for the ~12 tracked commodities (Soya DO, Soya Refined, Sunflower, Ricebran DO, etc.), with each row broken out into `factory_price`, `packing_cost_kg`, `with_gst_kg` and `with_gst_ltr`. The user can view any past day's records from the database (`/daily-price/db-list/?date=`), pull today's fresh prices with a fetch action (`/daily-price/fetch/` returns status + a preview of the fetched rows), and switch to a trend view that charts one line per commodity over a start/end date range (`/daily-price/trends/`). A highest/lowest summary (`/daily-price/highest-lowest/`) flags the single top and bottom priced commodity records in the selected range, e.g. Sunflower at 171.50 vs Ricebran DO at 137.28.

## How it helps

Daily commodity prices drive JIVO's cost base for domestic contracts and pack pricing; ops and directors open this page each morning to confirm the day's fetch landed and to see which oils moved. The trend chart and highest/lowest markers over a chosen range support buy/hold timing and rate-revision decisions.

## Backend endpoints

- [[endpoints/daily-price_db-list|`GET /daily-price/db-list/`]] — Historical daily commodity factory-price records (optionally for a date).
- [[endpoints/daily-price_fetch|`GET /daily-price/fetch/`]] — Fetch/refresh the latest daily commodity prices; returns status + preview.
- [[endpoints/daily-price_highest-lowest|`GET /daily-price/highest-lowest/`]] — Highest & lowest commodity prices over a date range.
- [[endpoints/daily-price_trends|`GET /daily-price/trends/`]] — Daily-price trend series (labels + datasets) for charting over a range.

## Key data & interactions

- Date picker (single `date` for the day's sheet) plus `start_date` / `end_date` range pickers for trends and highest/lowest.
- Fetch/Refresh action calling `/daily-price/fetch/`; shows `status`, row `count` (12 commodities) and a preview table before the data lands in the db-list.
- Price table columns: Commodity, Factory Price (₹/kg), Packing Cost/kg, With GST/kg, With GST/ltr, Date, Created By.
- Trend chart: one dataset per commodity (`labels` = dates like "Jun 18", `data` = factory prices) from `/daily-price/trends/`.
- Highest / Lowest cards showing the peak and floor commodity record (name, price, date) in the selected range.

## Related pages (same section)

- [[pages/jivo-rates|Jivo Rates]]
- [[pages/market-rates|Market Rates]]
- [[pages/our-rates|Our Rates]]


Linked: [[INDEX]] · [[API-INVENTORY]]
