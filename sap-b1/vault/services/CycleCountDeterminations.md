---
entity: CycleCountDeterminations
domain: system-other-1
readable: true
methods: [GET, PATCH]
rows_oil: 55
---
# CycleCountDeterminations
Per-warehouse setup (55 warehouses) of cycle-count scheduling rules that drive periodic inventory counting recommendations. Live rows in JIVO_OIL_HANADB: 55.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CycleCountDeterminations --top 5
./sapb1 query CycleCountDeterminations --count
./sapb1 query CycleCountDeterminations --select "WarehouseCode,CycleBy" --top 10
# cycle-count setup for one warehouse
./sapb1 query CycleCountDeterminations --filter "WarehouseCode eq '01'" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| WarehouseCode | Warehouse key |
| CycleBy | Counting grouping basis |
| CycleCountDeterminationSetupCollection | Per-cycle schedule lines |
## Connections
- Domain: [[system-other-1]]
- [[Warehouses]] via WarehouseCode — the warehouse the rules apply to
- [[InventoryCountings]] via generated count recommendations — countings driven by these cycles
- [[Items]] via item cycle-count codes — items picked up by cycle scheduling
