---
entity: SalesOpportunityReasonsSetup
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# SalesOpportunityReasonsSetup
Lookup list of win/loss reasons for closed sales opportunities; empty. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesOpportunityReasonsSetup --top 5
./sapb1 query SalesOpportunityReasonsSetup --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields SalesOpportunityReasonsSetup
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields SalesOpportunityReasonsSetup` when populated.

## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] via the win/loss reason on closed opportunity records
