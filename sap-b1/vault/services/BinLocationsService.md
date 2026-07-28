---
entity: BinLocationsService
domain: inventory-warehouse-1
readable: false
methods: ["BinLocationsService_GetList"]
rows_oil: null
---
# BinLocationsService
RPC list access to warehouse bin locations (the physical storage slots inside bin-enabled warehouses).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Warehouses]] — warehouses containing the bins
- [[Items]] — stock stored in the bins
