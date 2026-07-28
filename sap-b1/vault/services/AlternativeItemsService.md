---
entity: AlternativeItemsService
domain: inventory-warehouse-1
readable: false
methods: ["AlternativeItemsService_AddItem", "AlternativeItemsService_UpdateItem", "AlternativeItemsService_DeleteItem", "AlternativeItemsService_GetItem"]
rows_oil: null
---
# AlternativeItemsService
Manages alternative/substitute item mappings so a replacement item can be offered when the original is unavailable.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] — original and substitute items in each mapping
