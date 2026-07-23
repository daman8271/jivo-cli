---
title: Director Dashboard
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /reports/director-dashboard
section: Reports
---

# Director Dashboard

[[INDEX|JIVO EXIM]] › **Reports** › Director Dashboard

**Route:** `/reports/director-dashboard`  ·  **Web:** `https://exim.jivo.in/reports/director-dashboard`

## What this page does

Top-level rollup for directors built from `GET /director-inventorty/`: finished goods by warehouse (BH-EC, GP-FG), at-factory stock split into in_tank vs outside_factory, and pipeline buckets per lifecycle stage (in_contract, on_the_sea, mundra_port, otw, under_loading, at_refinery), each reported in both litres and MTS. Clicking into a stage drills down via `GET /stock-status/vehicle-report/?status=...` to vehicle-wise item detail (vendor, quantity, rate, ETA).

## How it helps

Gives a director the one-glance answer to "how much oil do we have and where is it" across the whole import pipeline, from contracted volume (e.g. ~798k litres in_contract) down to finished goods (~578k litres). Used for supply-cover and commitment decisions without wading through row-level reports.

## Backend endpoints

- [[endpoints/director-inventorty|`GET /director-inventorty/`]] — Director rollup: finished + at-factory + in-transit inventory by litre/MT.
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]] — Vehicle-wise stock grouped by a status.

## Key data & interactions

- KPI cards per lifecycle stage: in_contract, on_the_sea, mundra_port, otw (on the way), under_loading, at_refinery, at_factory (in_tank + outside_factory), finished — each with litres and MTS
- Finished-goods split by warehouse (BH-EC, GP-FG)
- LITERS / MTS unit toggle (both values come from the endpoint)
- Stage drill-down table via vehicle-report: vehicle_number, transporter, item_name, vendor_name, total_quantity_in_litre / _mts, rate, eta, arrival_date
- Refresh

## Related pages (same section)

- [[pages/dashboard|Dashboard]]
- [[pages/stock-dashboard|Stock Dashboard]]
- [[pages/warehouse-inventory|Warehouse Inventory]]
- [[pages/vehicle-report|Vehicle Report]]
- [[pages/contracts|Contracts]]
- [[pages/planning|Planning]]


Linked: [[INDEX]] · [[API-INVENTORY]]
