---
entity: StockTransferDraftService
domain: inventory-warehouse-1
readable: false
methods: ["StockTransferDraftService_GetApprovalTemplates", "StockTransferDraftService_HandleApprovalRequest"]
rows_oil: null
---
# StockTransferDraftService
Handles approval workflow steps for stock transfer draft documents.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[StockTransferDrafts]] — the draft documents being approved
- [[StockTransfers]] — posted transfers the drafts become
- [[ApprovalTemplates]] — approval templates applied to them
