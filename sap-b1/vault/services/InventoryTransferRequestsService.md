---
entity: InventoryTransferRequestsService
domain: inventory-warehouse-1
readable: false
methods: ["InventoryTransferRequestsService_GetApprovalTemplates", "InventoryTransferRequestsService_HandleApprovalRequest"]
rows_oil: null
---
# InventoryTransferRequestsService
Handles approval workflow steps for inventory transfer request documents between warehouses.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[InventoryTransferRequests]] — the transfer requests being approved
- [[StockTransfers]] — posted transfers the requests become
- [[ApprovalTemplates]] — approval templates applied to them
