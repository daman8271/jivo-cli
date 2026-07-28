---
entity: BlanketAgreementsService
domain: sales-ar
readable: false
methods: ["BlanketAgreementsService_GetBlanketAgreementList"]
rows_oil: null
---
# BlanketAgreementsService
RPC helper that returns the list of blanket sales agreements for pickers/lookups.
## Operations
- BlanketAgreementsService_GetBlanketAgreementList

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops BlanketAgreementsService`.
## Connections
- Domain: [[sales-ar]]
- [[BlanketAgreements]] — the agreement documents the list RPC enumerates
- [[BusinessPartners]] — customers the agreements are signed with
