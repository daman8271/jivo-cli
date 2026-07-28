---
entity: ItemGroups
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 10
---
# ItemGroups
Categorizes items into 10 groups (e.g. finished goods vs raw material) and sets their default G/L account determination and planning parameters. Live rows in JIVO_OIL_HANADB: 10.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ItemGroups --top 5
./sapb1 query ItemGroups --count
./sapb1 query ItemGroups --select "Number,GroupName,PlanningSystem,ProcurementMethod" --top 10
# Groups whose items are bought rather than made:
./sapb1 query ItemGroups --filter "ProcurementMethod eq 'bom_Buy'" --select "Number,GroupName" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Number | Group numeric key |
| GroupName | Group display name |
| InventoryAccount | Default stock G/L account |
| RevenuesAccount | Default revenue account |
| ExpensesAccount | Default expense account |
| CostAccount | Default COGS account |
| PlanningSystem | MRP planning method |
| ProcurementMethod | Buy or make |
| DefaultInventoryUoM | Default inventory unit |
| LeadTime | Procurement lead time days |
| CycleCode | Assigned counting cycle |
| DefaultUoMGroup | Default UoM group |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[Items]] via ItemsGroupCode on the item master
- [[ChartOfAccounts]] via the account-determination fields
- [[Warehouses]] via per-warehouse account overrides for the group
- [[InventoryCycles]] via CycleCode
- [[UnitOfMeasurementGroups]] via DefaultUoMGroup
