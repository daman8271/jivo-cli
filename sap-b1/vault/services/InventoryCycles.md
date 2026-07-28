---
entity: InventoryCycles
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# InventoryCycles
Defines recurring cycle-count schedules that drive periodic inventory counting alerts (unused). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query InventoryCycles --top 5
./sapb1 query InventoryCycles --count
./sapb1 query InventoryCycles --select "CycleCode,CycleName,Frequency,NextCountingDate" --top 10
# Cycles due for a count soon (if cycle counting is ever adopted):
./sapb1 query InventoryCycles --filter "NextCountingDate ge '2026-07-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| CycleCode | Cycle numeric key |
| CycleName | Cycle display name |
| Frequency | How often counts recur |
| NextCountingDate | Next scheduled count date |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[InventoryCountings]] via CycleCode on count documents
- [[ItemGroups]] via CycleCode default on item groups
- [[Warehouses]] via cycle assignment in item-warehouse settings
