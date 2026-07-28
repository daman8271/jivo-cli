---
entity: TaxWebSitesService
domain: financials-accounting-1
readable: false
methods: ["TaxWebSitesService_GetTaxWebSiteList", "TaxWebSitesService_GetDefaultWebSite"]
rows_oil: null
---
# TaxWebSitesService
Lists external tax web sites/services (e.g. US tax lookup providers) configured for automatic tax calculation, including the default provider.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[TaxWebSites]] — the entity set counterpart holding the provider records (query this instead)
