---
entity: GTIsService
domain: administration-setup-1
readable: false
methods: [Import]
rows_oil: null
---
# GTIsService
Imports Golden Tax Interface (GTI) data — the China VAT invoice interface — into SAP B1.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[PurchaseInvoices]] via imported GTI invoice data — Import feeds VAT invoice records tied to purchase documents
