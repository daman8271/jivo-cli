---
entity: FAAccountDeterminationsService
domain: financials-accounting-1
readable: false
methods: ["FAAccountDeterminationsService_GetList"]
rows_oil: null
---
# FAAccountDeterminationsService
Returns fixed-asset account determination sets mapping asset classes to G/L accounts for acquisition, depreciation and retirement postings.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[FAAccountDeterminations]] — the entity set counterpart holding the determination sets (query this instead)
- [[ChartOfAccounts]] — the G/L accounts each determination maps postings to
- [[AssetClasses]] — asset classes referencing a determination set (AccountDetermination)
