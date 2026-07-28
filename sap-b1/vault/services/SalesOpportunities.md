---
entity: SalesOpportunities
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# SalesOpportunities
CRM pipeline records tracking potential deals through stages to won/lost; CRM module unused in JIVO_OIL (0 rows). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesOpportunities --top 5
./sapb1 query SalesOpportunities --count
# Entity set is empty — discover the schema live if the CRM module is ever adopted:
./sapb1 fields SalesOpportunities
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields SalesOpportunities` when populated.

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode (prospect/customer)
- [[SalesPersons]] via SalesPerson (owner)
- [[SalesStages]] via stage lines (pipeline progression)
- [[SalesOpportunitySourcesSetup]] via Source (lead origin)
- [[SalesOpportunityCompetitorsSetup]] via competitor field on the deal
