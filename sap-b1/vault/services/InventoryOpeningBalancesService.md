---
entity: InventoryOpeningBalancesService
domain: inventory-warehouse-1
readable: false
methods: ["InventoryOpeningBalancesService_GetList"]
rows_oil: null
---
# InventoryOpeningBalancesService
RPC list access to inventory opening balance documents that seed initial stock quantities and values.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] — items whose opening stock was seeded
- [[Warehouses]] — warehouses the opening balances were booked into
