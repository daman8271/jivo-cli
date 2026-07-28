---
entity: OccurrenceCodesService
domain: financials-accounting-1
readable: false
methods: ["OccurrenceCodesService_GetList"]
rows_oil: null
---
# OccurrenceCodesService
Returns bank occurrence codes (Brazil localization) describing boleto/payment file events exchanged with banks.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[OccurrenceCodes]] — the entity set counterpart holding the occurrence code records (query this instead)
- House banks — codes describe events in files exchanged with house banks (catalog exposes [[HouseBankAccounts]], not a HouseBanks set)
