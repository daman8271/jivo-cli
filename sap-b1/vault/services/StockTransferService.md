---
entity: StockTransferService
domain: inventory-warehouse-1
readable: false
methods: ["StockTransferService_GetApprovalTemplates", "StockTransferService_HandleApprovalRequest"]
rows_oil: null
---
# StockTransferService
Handles approval workflow steps for posted inter-warehouse stock transfer documents.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[StockTransfers]] — the transfer documents being approved
- [[Warehouses]] — source and destination warehouses
- [[ApprovalTemplates]] — approval templates applied to them
