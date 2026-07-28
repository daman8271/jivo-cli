---
entity: DunningTermsService
domain: sales-ar
readable: false
methods: ["DunningTermsService_GetDunningTermList"]
rows_oil: null
---
# DunningTermsService
RPC helper returning the list of dunning terms used for overdue A/R reminder runs.
## Operations
- DunningTermsService_GetDunningTermList

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops DunningTermsService`.
## Connections
- Domain: [[sales-ar]]
- [[DunningTerms]] — the dunning-term master records the list RPC enumerates
- [[BusinessPartners]] — customers whose overdue balances get dunned under these terms
