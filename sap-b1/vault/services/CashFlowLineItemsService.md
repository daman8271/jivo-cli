---
entity: CashFlowLineItemsService
domain: inventory-warehouse-1
readable: false
methods: ["CashFlowLineItemsService_GetCashFlowLineItemList"]
rows_oil: null
---
# CashFlowLineItemsService
Lists the cash flow line item categories used to classify postings for cash flow statement reporting.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[inventory-warehouse-1]]
- [[ChartOfAccounts]] — accounts whose postings the line items classify
