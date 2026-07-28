---
entity: RouteStages
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# RouteStages
Defines production routing stages (steps a manufacturing order passes through); not configured in this database. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query RouteStages --top 5
./sapb1 query RouteStages --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[ProductionOrders]] via routing stage lines (StageID)
- [[ProductTrees]] via ProductTreeStages (StageId)
