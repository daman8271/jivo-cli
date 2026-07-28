---
entity: InventoryGenExitService
domain: inventory-warehouse-1
readable: false
methods: ["InventoryGenExitService_GetApprovalTemplates", "InventoryGenExitService_HandleApprovalRequest"]
rows_oil: null
---
# InventoryGenExitService
Handles approval workflow steps for Goods Issue (inventory general exit) documents.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[InventoryGenExits]] — the goods issue documents being approved
- [[ApprovalTemplates]] — approval templates applied to them
