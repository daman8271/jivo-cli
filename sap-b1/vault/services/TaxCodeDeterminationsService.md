---
entity: TaxCodeDeterminationsService
domain: financials-accounting-1
readable: false
methods: ["TaxCodeDeterminationsService_GetTaxCodeDeterminationList"]
rows_oil: null
---
# TaxCodeDeterminationsService
Lists tax code determination rules that auto-select the tax code on documents based on BP, item, and location criteria.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[TaxCodeDeterminations]] — the entity set counterpart holding the rule records (query this instead)
- [[VatGroups]] — VAT codes the rules resolve to
- [[SalesTaxCodes]] — sales tax codes the rules resolve to
- [[BusinessPartners]] — a rule criterion (CardCode / BP properties)
- [[Items]] — a rule criterion (ItemCode / item properties)
