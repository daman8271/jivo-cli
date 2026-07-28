---
entity: ResourceGroups
domain: production-mrp
readable: true
methods: ["GET ResourceGroups(id)", "GET ResourceGroups", "POST ResourceGroups", "PATCH ResourceGroups(id)", "DELETE ResourceGroups(id)"]
rows_oil: 1
---
# ResourceGroups
Categorizes production resources into groups with default cost-component names and rates (machine vs labor). Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ResourceGroups --top 5
./sapb1 query ResourceGroups --count
./sapb1 query ResourceGroups --select "Code,Name,Type,Cost1" --top 10
# machine-type groups only
./sapb1 query ResourceGroups --filter "Type eq 'rgtMachine'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Group code |
| Name | Group name |
| Type | Machine or labor group |
| NumOfUnitsText | Units-of-measure label |
| Cost1 | Default cost rate 1 |
| CostName1 | Cost component 1 name |
| Cost2 | Default cost rate 2 |
| CostName2 | Cost component 2 name |
| Cost3 | Default cost rate 3 |
| CostName3 | Cost component 3 name |

## Connections
- Domain: [[production-mrp]]
- [[Resources]] via Group — resources assigned to this group
