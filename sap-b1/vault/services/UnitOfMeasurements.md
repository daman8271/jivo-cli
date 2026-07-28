---
entity: UnitOfMeasurements
domain: inventory-warehouse-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 4
---
# UnitOfMeasurements
Master catalog of individual units of measure with physical dimensions (volume, weight, size) referenced by UoM groups and items. Live rows in JIVO_OIL_HANADB: 4.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UnitOfMeasurements --top 5
./sapb1 query UnitOfMeasurements --count
./sapb1 query UnitOfMeasurements --select "AbsEntry,Code,Name,InternationalSymbol" --top 10
# Units that carry a defined physical volume
./sapb1 query UnitOfMeasurements --filter "Volume gt 0"
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal UoM key |
| Code | Unit short code |
| Name | Unit display name |
| InternationalSymbol | Standard symbol (e.g., L) |
| Volume | Defined unit volume |
| VolumeUnit | Volume measurement unit |
| Weight1 | Defined unit weight |
| Weight1Unit | Weight measurement unit |
| Length1 | Unit length dimension |
| Width1 | Unit width dimension |
| Height1 | Unit height dimension |

## Connections
- Domain: [[inventory-warehouse-2]]
- [[UnitOfMeasurementGroups]] via BaseUoM / conversion lines — groups built from these units
- [[Items]] via InventoryUoMEntry and UoM assignments — items measured in these units
