---
entity: PickListsService
domain: inventory-warehouse-1
readable: false
methods: ["PickListsService_Close", "PickListsService_UpdateReleasedAllocation"]
rows_oil: null
---
# PickListsService
Closes pick lists and updates released stock allocations in the warehouse pick-and-pack process.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[PickLists]] — the pick lists being closed/updated
- [[Orders]] — sales orders the picks fulfil
- [[DeliveryNotes]] — deliveries created from completed picks
