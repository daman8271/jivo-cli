---
entity: ResourceCapacities
domain: production-mrp
readable: true
methods: ["GET ResourceCapacities(id)", "GET ResourceCapacities", "POST ResourceCapacities", "PATCH ResourceCapacities(id)", "DELETE ResourceCapacities(id)"]
rows_oil: 19003
---
# ResourceCapacities
Per-day capacity ledger for each resource and warehouse — available/committed/consumed capacity entries driving production scheduling. Live rows in JIVO_OIL_HANADB: 19003.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ResourceCapacities --top 5
./sapb1 query ResourceCapacities --count
./sapb1 query ResourceCapacities --select "Code,Date,Type,Capacity" --top 10
# capacity entries for the current month
./sapb1 query ResourceCapacities --filter "Date ge '2026-07-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Id | Internal ledger entry key |
| Code | Resource code |
| Date | Capacity day |
| Type | Available/committed/consumed entry type |
| Capacity | Capacity amount (units) |
| SingleRunCapacity | Capacity per single run |
| Warehouse | Warehouse the capacity applies to |
| BaseType | Base document type |
| BaseEntry | Base document key |
| BaseLineNum | Base document line |
| OwningType | Owning object type |
| OwningEntry | Owning object key |
| SourceType | Source document type |
| SourceEntry | Source document key |

## Connections
- Domain: [[production-mrp]]
- [[Resources]] via Code — the resource this day-entry belongs to
- [[Warehouses]] via Warehouse — warehouse the capacity is booked in
- [[ProductionOrders]] via BaseType/BaseEntry — work order consuming the capacity
