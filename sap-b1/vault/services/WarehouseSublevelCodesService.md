---
entity: WarehouseSublevelCodesService
domain: inventory-warehouse-1
readable: false
methods: ["WarehouseSublevelCodesService_GetList"]
rows_oil: null
---
# WarehouseSublevelCodesService
Lists sublevel codes used to structure bin location hierarchies within bin-managed warehouses.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Warehouses]] — bin-managed warehouses the sublevels belong to
- [[BinLocations]] — bins structured by the sublevel codes
