---
entity: BinLocationFieldsService
domain: inventory-warehouse-1
readable: false
methods: ["BinLocationFieldsService_GetList"]
rows_oil: null
---
# BinLocationFieldsService
Lists the field/segment definitions that make up bin location codes in bin-managed warehouses.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[BinLocations]] — bin codes built from these segments
- [[Warehouses]] — warehouses whose bin code structure this defines
