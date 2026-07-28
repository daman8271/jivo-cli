---
entity: CockpitsService
domain: administration-setup-1
readable: false
methods: [CockpitsService_GetCockpitList, CockpitsService_PublishCockpit, CockpitsService_GetUserCockpitList, CockpitsService_GetTemplateCockpitList]
rows_oil: null
---
# CockpitsService
Manages and lists user dashboard cockpits (personal and template) in the B1 client UI.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Users]] — each personal cockpit belongs to a user (UserCode)
