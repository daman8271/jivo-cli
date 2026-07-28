---
entity: UnitOfMeasurementGroupsService
domain: inventory-warehouse-1
readable: false
methods: ["UnitOfMeasurementGroupsService_GetList"]
rows_oil: null
---
# UnitOfMeasurementGroupsService
RPC list access to UoM groups that define conversion rules between base and alternate units for items.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[UnitOfMeasurementGroups]] — the UoM groups this service lists
- [[UnitOfMeasurements]] — units the groups convert between
- [[Items]] — items assigned to each group
