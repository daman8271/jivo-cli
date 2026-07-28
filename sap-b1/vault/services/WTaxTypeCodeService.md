---
entity: WTaxTypeCodeService
domain: financials-accounting-1
readable: false
methods: [WTaxTypeCodeService_GetWTaxTypeCodeList]
rows_oil: null
---
# WTaxTypeCodeService
RPC helper that returns the list of withholding-tax type codes configured in the company.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]). It is a function service (no entity set), so the CLI cannot `query` it; entity sets are the read path. Browse its catalogued operations offline with `./sapb1 ops WTaxTypeCodeService`.

## Operations
- WTaxTypeCodeService_GetWTaxTypeCodeList

## Connections
- Domain: [[financials-accounting-1]]
- [[WithholdingTaxCodes]] — the entity set holding the withholding-tax codes this service lists by type
