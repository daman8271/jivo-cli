---
entity: DunningTerms
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# DunningTerms
Setup for dunning rules (levels, intervals, fees) applied to overdue customers; unused in JIVO_OIL. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DunningTerms --top 5
./sapb1 query DunningTerms --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields DunningTerms
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields DunningTerms` when populated.

## Connections
- Domain: [[sales-ar]]
- [[DunningLetters]] via dunning term code (letters generated under a term)
- [[BusinessPartners]] via the dunning term assigned on the customer master
