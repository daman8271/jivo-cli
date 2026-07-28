---
entity: CampaignResponseTypeService
domain: business-partners-crm
readable: false
methods: [CampaignResponseTypeService_GetResponseTypeList]
rows_oil: null
---
# CampaignResponseTypeService
RPC returning the catalog of campaign response types.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[business-partners-crm]]
- [[CampaignResponseType]] — the response-type catalog (read it there instead)
- [[Campaigns]] — campaigns whose target responses use these types
