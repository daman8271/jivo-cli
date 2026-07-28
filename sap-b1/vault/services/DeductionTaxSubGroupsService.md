---
entity: DeductionTaxSubGroupsService
domain: financials-accounting-1
readable: false
methods: ["DeductionTaxSubGroupsService_GetDeductionTaxSubGroupList"]
rows_oil: null
---
# DeductionTaxSubGroupsService
Lists withholding/deduction tax sub-groups (e.g. Israel/India TDS sub-classifications) under deduction tax groups.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[DeductionTaxSubGroups]] — the entity set counterpart holding the sub-group records (query this instead)
- [[DeductionTaxGroups]] — parent groups each sub-group belongs to (GroupCode)
- [[WithholdingTaxCodes]] — withholding tax codes classified by these sub-groups
