---
entity: PartnersSetupsService
domain: business-partners-crm
readable: false
methods: [PartnersSetupsService_GetList]
rows_oil: null
---
# PartnersSetupsService
RPC returning partner setup/configuration records (BP-related setup definitions).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] — BP master the setup definitions apply to
