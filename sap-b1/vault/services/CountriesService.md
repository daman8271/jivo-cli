---
entity: CountriesService
domain: administration-setup-1
readable: false
methods: [CountriesService_GetCountryList]
rows_oil: null
---
# CountriesService
Lists country master data used in business partner and company addresses.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Countries]] — the country records this RPC lists (Code)
- [[States]] — states nest under a country (Country)
- [[Currencies]] — each country carries a default currency (Currency)
