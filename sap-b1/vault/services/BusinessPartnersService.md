---
entity: BusinessPartnersService
domain: business-partners-crm
readable: false
methods: [BusinessPartnersService_CreateOpenBalance]
rows_oil: null
---
# BusinessPartnersService
Write-side helper to create an opening balance journal for a business partner (never used here — read-only mandate).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] — the BP the opening balance would post against
- [[ChartOfAccounts]] — offset account for the opening balance journal
