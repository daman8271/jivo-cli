---
title: Contracts
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /reports/contracts
section: Reports
---

# Contracts

[[INDEX|JIVO EXIM]] › **Reports** › Contracts

**Route:** `/reports/contracts`  ·  **Web:** `https://exim.jivo.in/reports/contracts`

## What this page does

Lists domestic purchase contracts by loading `GET /stock-status/?status=IN_CONTRACT`. Each row is a contract line: item (e.g. RM0MKG MUSTARD KACHI GHANI), vendor (e.g. AWL AGRI BUSINESS LIMITED), rate per KG and per litre, contracted quantity in KG and litres, source location, payment_status, and the contract_start / contract_end window. From here users track which contracted volumes have not yet moved into the physical pipeline (ON_THE_SEA, ON_THE_WAY, etc.).

## How it helps

Ops and procurement open this page to see how much oil is locked in at what rate with which vendor, and which contracts are nearing their contract_end date without lifting. It answers "what have we bought that hasn't shipped yet" and flags UNPAID lines for accounts follow-up.

## Backend endpoints

- [[endpoints/stock-status|`GET /stock-status/`]] — Create a stock-status record.

## Key data & interactions

- Contract table: item_code / item_name, vendor_name, rate (per KG) and rate_in_litres, quantity and quantity_in_litre, location, payment_status, contract_start, contract_end
- Status filter fixed to `status=IN_CONTRACT` via the `status` query param of `/stock-status/`
- KG / MTS / LITERS unit toggle switching between quantity and quantity_in_litre columns
- Filters by RM item code and vendor; Refresh to refetch

## Related pages (same section)

- [[pages/dashboard|Dashboard]]
- [[pages/stock-dashboard|Stock Dashboard]]
- [[pages/director-dashboard|Director Dashboard]]
- [[pages/warehouse-inventory|Warehouse Inventory]]
- [[pages/vehicle-report|Vehicle Report]]
- [[pages/planning|Planning]]


Linked: [[INDEX]] · [[API-INVENTORY]]
