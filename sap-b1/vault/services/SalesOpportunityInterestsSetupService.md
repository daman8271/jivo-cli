---
entity: SalesOpportunityInterestsSetupService
domain: sales-ar
readable: false
methods: ["SalesOpportunityInterestsSetupService_GetSalesOpportunityInterestSetupList"]
rows_oil: null
---
# SalesOpportunityInterestsSetupService
RPC helper listing the interest-level master values used on sales opportunities.
## Operations
- SalesOpportunityInterestsSetupService_GetSalesOpportunityInterestSetupList

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops SalesOpportunityInterestsSetupService`.
## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] — the opportunity documents that use these interest levels
