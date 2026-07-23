---
title: Jivo Rates
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /commodity/jivo-rates
section: Commodity Price
---

# Jivo Rates

[[INDEX|JIVO EXIM]] › **Commodity Price** › Jivo Rates

**Route:** `/commodity/jivo-rates`  ·  **Web:** `https://exim.jivo.in/commodity/jivo-rates`

## What this page does

Shows JIVO's own consumer pack rates: one row per pack type and commodity combination (e.g. Pouch 1 Ltr SOYA at ₹154.00, Pouch 1 Ltr Mustard at ₹174.00), around 25 rows per day. A fetch action (`GET /jivo-rate/fetch/`) pulls the latest rates and returns a `status`, row `count` and `preview_data` (pack_type, commodity, rate, date, created_by) so the user can confirm today's rate sheet is current.

## How it helps

This is the record of what JIVO actually charges per pack; sales and finance users open it to quote customers and to check the day's pack rates against commodity cost moves seen on Daily Price and Market Rates. A stale fetch date is the signal that the rate sheet has not been updated.

## Backend endpoints

- [[endpoints/jivo-rate_fetch|`GET /jivo-rate/fetch/`]] — Fetch/refresh latest JIVO pack rates; returns status + preview.

## Key data & interactions

- Fetch/Refresh action calling `/jivo-rate/fetch/`; shows `status: success` and fetched row `count` (~25).
- Rate table columns: Pack Type (Pouch 1 Ltr, etc.), Commodity (SOYA, Mustard, ...), Rate (₹), Date, Created By.
- Rows group naturally by pack type across commodities, giving a pack-size x commodity rate grid for the fetched date.

## Related pages (same section)

- [[pages/daily-price|Daily Price]]
- [[pages/market-rates|Market Rates]]
- [[pages/our-rates|Our Rates]]


Linked: [[INDEX]] · [[API-INVENTORY]]
