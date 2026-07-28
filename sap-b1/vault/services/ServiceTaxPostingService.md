---
entity: ServiceTaxPostingService
domain: financials-accounting-1
readable: false
methods: ["ServiceTaxPostingService_PostServiceTax", "ServiceTaxPostingService_GetTaxableDeliveries"]
rows_oil: null
---
# ServiceTaxPostingService
India-localization utility that finds taxable deliveries and posts the corresponding service tax liability to the ledger.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[DeliveryNotes]] — the taxable deliveries it scans (DocEntry)
- [[JournalEntries]] — the service tax liability it posts lands as journal entries
- [[SalesTaxCodes]] — the service tax codes driving the liability amounts
