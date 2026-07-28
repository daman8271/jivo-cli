---
entity: BusinessPartnerPropertiesService
domain: business-partners-crm
readable: false
methods: [BusinessPartnerPropertiesService_GetBusinessPartnerPropertyList]
rows_oil: null
---
# BusinessPartnerPropertiesService
RPC to fetch the list of the 64 BP property flags used to classify business partners.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartnerProperties]] — the property-flag catalog (read it there instead)
- [[BusinessPartners]] — BPs classified by these flags
