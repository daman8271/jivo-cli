---
entity: InventoryGenEntryService
domain: inventory-warehouse-1
readable: false
methods: ["InventoryGenEntryService_GetApprovalTemplates", "InventoryGenEntryService_HandleApprovalRequest"]
rows_oil: null
---
# InventoryGenEntryService
Handles approval workflow steps for Goods Receipt (inventory general entry) documents.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[InventoryGenEntries]] — the goods receipt documents being approved
- [[ApprovalTemplates]] — approval templates applied to them
