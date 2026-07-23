---
title: Planning
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /reports/planning
section: Reports
---

# Planning

[[INDEX|JIVO EXIM]] › **Reports** › Planning

**Route:** `/reports/planning`  ·  **Web:** `https://exim.jivo.in/reports/planning`

## What this page does

Shows SAP monthly production/procurement planning. `GET /sap-sync/planned-months/` fills a month picker (Code like "Nov-2024", StartDate/EndDate); selecting a month calls `GET /sap-sync/monthly-planning/?monthId=<AbsID>` and lists planned quantity per oil sub-group (U_Sub_Group: MUSTARD, OLIVE, etc., ~13 rows).

## How it helps

Lets ops compare the SAP plan for a month (e.g. 940,174 units of MUSTARD) against what is actually contracted and in the pipeline, so procurement gaps surface before the month starts. It is the reference point for deciding what still needs to be bought.

## Backend endpoints

- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]] — Monthly SAP planning rows for a given month id.
- [[endpoints/sap-sync_planned-months|`GET /sap-sync/planned-months/`]] — Available planning months (SAP).

## Key data & interactions

- Planning-month dropdown from planned-months (Code, e.g. "Nov-2024"; ~23 months available); selection passes AbsID as `monthId`
- Planning table: U_Sub_Group (oil category) and planned Quantity
- Month StartDate / EndDate shown for the selected plan
- Refresh to re-pull from SAP

## Related pages (same section)

- [[pages/dashboard|Dashboard]]
- [[pages/stock-dashboard|Stock Dashboard]]
- [[pages/director-dashboard|Director Dashboard]]
- [[pages/warehouse-inventory|Warehouse Inventory]]
- [[pages/vehicle-report|Vehicle Report]]
- [[pages/contracts|Contracts]]


Linked: [[INDEX]] · [[API-INVENTORY]]
