---
entity: SalesOpportunityInterestsSetup
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# SalesOpportunityInterestsSetup
Lookup list of interest ranges/areas for classifying sales opportunities; empty. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesOpportunityInterestsSetup --top 5
./sapb1 query SalesOpportunityInterestsSetup --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields SalesOpportunityInterestsSetup
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields SalesOpportunityInterestsSetup` when populated.

## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] via the interest classification on opportunity records
