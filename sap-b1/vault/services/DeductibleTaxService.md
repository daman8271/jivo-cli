---
entity: DeductibleTaxService
domain: financials-accounting-1
readable: false
methods: ["DeductibleTaxService_GetList"]
rows_oil: null
---
# DeductibleTaxService
Returns deductible-tax definitions specifying what portion of input tax is recoverable versus expensed.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[DeductibleTaxes]] — the entity set counterpart holding the deductible-tax definitions (query this instead)
- [[VatGroups]] — VAT groups whose input tax these definitions split into recoverable vs expensed
- [[SalesTaxCodes]] — tax codes affected by deductibility rules
