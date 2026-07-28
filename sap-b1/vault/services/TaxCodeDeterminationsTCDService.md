---
entity: TaxCodeDeterminationsTCDService
domain: financials-accounting-1
readable: false
methods: ["TaxCodeDeterminationsTCDService_GetTaxCodeDeterminationTCDList"]
rows_oil: null
---
# TaxCodeDeterminationsTCDService
Returns the newer condition-based (TCD) tax determination rules used by localizations like India GST to derive tax codes on marketing documents.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[TaxCodeDeterminationsTCD]] — the entity set counterpart holding the TCD rule records (query this instead)
- [[VatGroups]] — GST/VAT codes the conditions resolve to
- [[SalesTaxCodes]] — sales tax codes the conditions resolve to
