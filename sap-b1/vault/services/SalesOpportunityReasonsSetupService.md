---
entity: SalesOpportunityReasonsSetupService
domain: sales-ar
readable: false
methods: ["SalesOpportunityReasonsSetupService_GetSalesOpportunityReasonSetupList"]
rows_oil: null
---
# SalesOpportunityReasonsSetupService
RPC helper listing win/loss reason master values used on sales opportunities.
## Operations
- SalesOpportunityReasonsSetupService_GetSalesOpportunityReasonSetupList

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops SalesOpportunityReasonsSetupService`.
## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] — the opportunity documents that record these win/loss reasons
