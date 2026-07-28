---
entity: ServiceCallOrigins
domain: service-contracts
readable: true
methods: ["GET ServiceCallOrigins(id)", "GET ServiceCallOrigins", "POST ServiceCallOrigins", "PATCH ServiceCallOrigins(id)", "DELETE ServiceCallOrigins(id)"]
rows_oil: 3
---
# ServiceCallOrigins
Catalog of how service calls were reported (e.g. phone, email, web) — 3 seed values in JIVO_OIL. Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ServiceCallOrigins --top 5
./sapb1 query ServiceCallOrigins --count
./sapb1 query ServiceCallOrigins --select "OriginID,Name,Active" --top 10
# active origin codes only
./sapb1 query ServiceCallOrigins --filter "Active eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| OriginID | Origin code |
| Name | Origin name |
| Description | Longer description |
| Active | Active/inactive flag |

## Connections
- Domain: [[service-contracts]]
- [[ServiceCalls]] via Origin — tickets tagged with this origin
