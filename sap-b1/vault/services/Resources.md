---
entity: Resources
domain: production-mrp
readable: true
methods: ["GET Resources(id)", "GET Resources", "POST Resources", "PATCH Resources(id)", "DELETE Resources(id)", "POST Resources(id)/CreateLinkedItem"]
rows_oil: 7
---
# Resources
Master data for production resources (machines/labor lines) with costs, group, default warehouse, and optional linked item — 7 resources in the oil plant. Live rows in JIVO_OIL_HANADB: 7.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Resources --top 5
./sapb1 query Resources --count
./sapb1 query Resources --select "Code,Name,Type,DefaultWarehouse" --top 10
# active resources only
./sapb1 query Resources --filter "Active eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Resource code |
| Name | Resource name |
| ForeignName | Foreign-language name |
| Group | Resource group code |
| Type | Machine or labor |
| Active | Active/inactive flag |
| DefaultWarehouse | Default warehouse code |
| LinkedItem | Linked inventory item |
| IssueMethod | Backflush or manual issue |
| Cost1 | Cost component rate 1 |
| Cost2 | Cost component rate 2 |
| Cost3 | Cost component rate 3 |
| Number | Number of units |
| CodeBar | Barcode |

## Connections
- Domain: [[production-mrp]]
- [[ResourceGroups]] via Group — cost/type group of the resource
- [[Warehouses]] via DefaultWarehouse — default capacity warehouse
- [[Items]] via LinkedItem — inventory item mirroring the resource
- [[ResourceCapacities]] via Code — daily capacity ledger entries
- [[ProductionOrders]] via resource BOM lines — work orders consuming the resource
