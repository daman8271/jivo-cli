---
entity: UnitOfMeasurementGroups
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 4
---
# UnitOfMeasurementGroups
Groups of units of measure with conversion definitions to a base UoM, assigned to items for multi-UoM handling (e.g., bottle/box/litre). Live rows in JIVO_OIL_HANADB: 4.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UnitOfMeasurementGroups --top 5
./sapb1 query UnitOfMeasurementGroups --count
./sapb1 query UnitOfMeasurementGroups --select "AbsEntry,Code,Name,BaseUoM" --top 10
# Look up one group by its code
./sapb1 query UnitOfMeasurementGroups --filter "Code eq 'Manual'"
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal group key |
| Code | Group short code |
| Name | Group display name |
| BaseUoM | Base unit of group |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[UnitOfMeasurements]] via BaseUoM and conversion lines — the units this group converts between
- [[Items]] via UoMGroupEntry — items priced/stocked in this group's units
