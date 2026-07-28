---
entity: InventoryCountingsService
domain: inventory-warehouse-1
readable: false
methods: ["InventoryCountingsService_GetList"]
rows_oil: null
---
# InventoryCountingsService
RPC list access to physical inventory counting documents used for stock-take reconciliation.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[InventoryCountings]] — the counting documents this service lists
- [[Items]] — items being counted
- [[Warehouses]] — warehouses where counts run
