---
entity: UnitOfMeasurementsService
domain: inventory-warehouse-1
readable: false
methods: ["UnitOfMeasurementsService_GetList"]
rows_oil: null
---
# UnitOfMeasurementsService
RPC list access to the master list of units of measure (e.g. litre, carton, piece).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[UnitOfMeasurements]] — the UoM master this service lists
- [[UnitOfMeasurementGroups]] — groups that combine the units into conversion sets
