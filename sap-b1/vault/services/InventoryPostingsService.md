---
entity: InventoryPostingsService
domain: inventory-warehouse-1
readable: false
methods: ["InventoryPostingsService_GetList", "InventoryPostingsService_SetCopyOption"]
rows_oil: null
---
# InventoryPostingsService
RPC access to inventory posting documents that book count differences after a stock take.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[InventoryCountings]] — counting documents whose differences get posted
- [[Items]] — items adjusted by the postings
- [[Warehouses]] — warehouses where adjustments land
