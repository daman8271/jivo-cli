---
entity: SalesStages
domain: sales-ar
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# SalesStages
Defines pipeline stages (with closing percentages) for sales opportunities; empty since CRM is unused. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesStages --top 5
./sapb1 query SalesStages --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields SalesStages
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields SalesStages` when populated.

## Connections
- Domain: [[sales-ar]]
- [[SalesOpportunities]] via stage number on opportunity stage lines
