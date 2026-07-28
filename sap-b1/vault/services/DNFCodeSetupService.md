---
entity: DNFCodeSetupService
domain: administration-setup-1
readable: false
methods: [DNFCodeSetupService_GetDNFCodeSetupList]
rows_oil: null
---
# DNFCodeSetupService
Lists Brazil DNF (fiscal declaration) code setup entries for item tax reporting (Brazil localization only).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Items]] — DNF codes classify items for Brazilian fiscal declarations (ItemCode)
