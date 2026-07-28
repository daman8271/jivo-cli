---
entity: CampaignsService
domain: business-partners-crm
readable: true
methods: [CampaignsService_GetList]
rows_oil: null
---
# CampaignsService
Function service returning the list of marketing campaigns.

## Operations
- `CampaignsService_GetList` (GET) — enumerate marketing campaigns
- `CampaignsService_GetList` (POST) — same list via POST invocation

Entity sets are the read path in the CLI — read the master data via [[Campaigns]]. Browse this service's operations with `./sapb1 ops CampaignsService`.

## Connections
- Domain: [[business-partners-crm]]
- [[Campaigns]] — the entity set this service enumerates (CampaignNumber)
