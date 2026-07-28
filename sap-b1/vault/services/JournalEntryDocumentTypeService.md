---
entity: JournalEntryDocumentTypeService
domain: financials-accounting-1
readable: false
methods: ["JournalEntryDocumentTypeService_GetList"]
rows_oil: null
---
# JournalEntryDocumentTypeService
Returns the document-type codes assignable to journal entries for classification and reporting.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[JournalEntryDocumentTypes]] — the entity set counterpart holding the document-type codes (query this instead)
- [[JournalEntries]] — journal entries carry one of these document-type codes
