---
entity: CycleCountDeterminationsService
domain: administration-setup-1
readable: false
methods: [CycleCountDeterminationsService_GetList]
rows_oil: null
---
# CycleCountDeterminationsService
Lists cycle-count determination rules that schedule periodic inventory counting per warehouse/item group.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Warehouses]] — each rule is scoped to a warehouse (WarehouseCode)
- [[Items]] — counted stock is item-level (ItemCode)
- [[InventoryCycles]] — rules reference an inventory cycle for the counting cadence (CycleCode)
