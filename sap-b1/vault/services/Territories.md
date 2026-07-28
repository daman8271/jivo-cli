---
entity: Territories
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# Territories
Hierarchical sales-territory master (parent/child regions) used to segment business partners and sales activity geographically. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Territories --top 5
./sapb1 query Territories --count
./sapb1 query Territories --select "TerritoryID,Description,Parent,Inactive" --top 10
# only active territories:
./sapb1 query Territories --filter "Inactive eq 'tNO'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| TerritoryID | Territory's numeric key |
| Description | Territory name |
| Parent | Parent territory ID (hierarchy) |
| LocationIndex | Position within the tree |
| Inactive | Active/inactive flag |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via Territory — partners are assigned to a territory
- [[SalesPersons]] via territory assignment — reps are mapped to territories
- [[SalesOpportunities]] via Territory — opportunities carry the territory ID
