---
title: Exchange Rates
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /exim-rates
section: Exchange Rates
---

# Exchange Rates

[[INDEX|JIVO EXIM]] › **Exchange Rates** › Exchange Rates

**Route:** `/exim-rates`  ·  **Web:** `https://exim.jivo.in/exim-rates`

## What this page does

Shows the current customs (CBIC) exchange rate notification for foreign currencies against the INR. On load the page calls `GET /exim-rates/fetch/`, which returns roughly 23 currencies (Australian Dollar, Bahraini Dinar, US Dollar, etc.), each with a separate `import` and `export` rate, the notification `date` (e.g. 2026-07-15) and the customs `notification_no` (e.g. 20/2026). The user reads the table and can re-fetch to pull the latest notification; there are no filters or write actions on this page.

## How it helps

Customs duty on JIVO's edible-oil imports is assessed at these notified rates, not market spot rates, so ops and finance users open this page to know exactly which rate applies when costing a shipment or checking a bill of entry. Having the current notification number and date in the app removes the need to look up CBIC circulars manually and keeps landed-cost and contract calculations consistent across the team.

## Backend endpoints

- [[endpoints/exim-rates_fetch|`GET /exim-rates/fetch/`]] — Fetch/refresh custom exchange (EXIM) rates.

## Key data & interactions

- Rates table with columns: Currency, Import rate (INR), Export rate (INR)
- Header showing the notification date (e.g. 15 Jul 2026) and customs Notification No. (e.g. 20/2026) that all listed rates belong to
- Refresh action that re-calls `GET /exim-rates/fetch/` to pull the latest notified rates
- Read-only page: no filters, unit toggles, or edit controls; one row per currency (~23 currencies)

## Related pages (same section)

- _(none)_


Linked: [[INDEX]] · [[API-INVENTORY]]
