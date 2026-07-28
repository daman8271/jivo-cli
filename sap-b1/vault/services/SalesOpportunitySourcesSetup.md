---
entity: SalesOpportunitySourcesSetup
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# SalesOpportunitySourcesSetup
Lookup list of lead sources (e.g. referral, web) for sales opportunities; empty. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesOpportunitySourcesSetup --top 5
./sapb1 query SalesOpportunitySourcesSetup --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields SalesOpportunitySourcesSetup
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields SalesOpportunitySourcesSetup` when populated.

## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] via Source (lead origin) on opportunity records
