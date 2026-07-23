---
title: Vehicle Report
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /reports/vehicle-report
section: Reports
---

# Vehicle Report

[[INDEX|JIVO EXIM]] › **Reports** › Vehicle Report

**Route:** `/reports/vehicle-report`  ·  **Web:** `https://exim.jivo.in/reports/vehicle-report`

## What this page does

Vehicle-wise view of in-transit stock from `GET /stock-status/vehicle-report/?status=<status>`: rows are grouped by vehicle_number and transporter, each carrying one or more item lines (item_name, vendor_name, total_quantity_in_litre and _mts, rate, eta, arrival_date, job_work). Underlying row-level data comes from `GET /stock-status/` filtered by the same status param, so the same lifecycle statuses (IN_CONTRACT through COMPLETED) drive both.

## How it helps

Logistics tracking per truck/tanker: which vehicle is carrying which oil from which vendor, its ETA, and whether it has arrived. Ops open it to chase transporters on delayed loads and to plan unloading slots at the factory.

## Backend endpoints

- [[endpoints/stock-status|`GET /stock-status/`]] — Create a stock-status record.
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]] — Vehicle-wise stock grouped by a status.

## Key data & interactions

- Status filter (`status` param): ON_THE_WAY, UNDER_LOADING, AT_REFINERY, etc., selecting which pipeline stage the report covers
- Groups per vehicle_number + transporter, expandable to item lines
- Item-line columns: item_code / item_name, vendor_name, total_quantity_in_litre, total_quantity_in_mts, rate, eta, arrival_date, job_work
- MTS / LITERS unit toggle; a "no vehicle assigned" group for null vehicle_number rows; Refresh

## Related pages (same section)

- [[pages/dashboard|Dashboard]]
- [[pages/stock-dashboard|Stock Dashboard]]
- [[pages/director-dashboard|Director Dashboard]]
- [[pages/warehouse-inventory|Warehouse Inventory]]
- [[pages/contracts|Contracts]]
- [[pages/planning|Planning]]


Linked: [[INDEX]] · [[API-INVENTORY]]
