---
entity: ServiceCallTypes
domain: service-contracts
readable: true
methods: ["GET ServiceCallTypes(id)", "GET ServiceCallTypes", "POST ServiceCallTypes", "PATCH ServiceCallTypes(id)", "DELETE ServiceCallTypes(id)"]
rows_oil: 0
---
# ServiceCallTypes
Catalog of service-call categories (e.g. repair, maintenance, inquiry) — empty here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceCallTypes --top 5
./sapb1 query ServiceCallTypes --count
./sapb1 query ServiceCallTypes --select "CallTypeID,Name,Active" --top 10
# active call types only
./sapb1 query ServiceCallTypes --filter "Active eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| CallTypeID | Call type code |
| Name | Call type name |
| Description | Longer description |
| Active | Active/inactive flag |

## Connections
- Domain: [[service-contracts]]
- [[ServiceCalls]] via CallType — tickets categorized under this type
