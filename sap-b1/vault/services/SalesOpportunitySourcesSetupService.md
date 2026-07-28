---
entity: SalesOpportunitySourcesSetupService
domain: sales-ar
readable: false
methods: ["SalesOpportunitySourcesSetupService_GetSalesOpportunitySourceSetupList"]
rows_oil: null
---
# SalesOpportunitySourcesSetupService
RPC helper listing the lead/opportunity source master values used on sales opportunities.
## Operations
- SalesOpportunitySourcesSetupService_GetSalesOpportunitySourceSetupList

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops SalesOpportunitySourcesSetupService`.
## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] — the opportunity documents that tag these lead sources
