---
entity: SalesOpportunityCompetitorsSetupService
domain: sales-ar
readable: false
methods: ["SalesOpportunityCompetitorsSetupService_GetSalesOpportunityCompetitorSetupList"]
rows_oil: null
---
# SalesOpportunityCompetitorsSetupService
RPC helper listing the competitor master values used on sales opportunities.
## Operations
- SalesOpportunityCompetitorsSetupService_GetSalesOpportunityCompetitorSetupList

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops SalesOpportunityCompetitorsSetupService`.
## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] — the opportunity documents that tag these competitor values
