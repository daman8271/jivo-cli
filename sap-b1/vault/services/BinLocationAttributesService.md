---
entity: BinLocationAttributesService
domain: inventory-warehouse-1
readable: false
methods: ["BinLocationAttributesService_GetList"]
rows_oil: null
---
# BinLocationAttributesService
Lists the definable attribute dimensions used to classify warehouse bin locations.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[BinLocations]] — bins these attributes classify
- [[Warehouses]] — bin-managed warehouses the attributes apply in
