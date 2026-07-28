---
entity: CreditLinesService
domain: administration-setup-1
readable: false
methods: [CreditLinesService_GetCreditLine, CreditLinesService_GetValidCreditLineList]
rows_oil: null
---
# CreditLinesService
Retrieves bank credit line definitions and the currently valid credit lines available to the company.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[BusinessPartners]] — credit lines can be tied to a partner (CardCode)
- [[HouseBankAccounts]] — the house bank account granting the credit line (the catalog exposes house banks as HouseBankAccounts)
