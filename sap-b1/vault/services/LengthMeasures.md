---
entity: LengthMeasures
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 6
---
# LengthMeasures
Length unit-of-measure lookup (mm-based conversions) used for item dimension fields. Live rows in JIVO_OIL_HANADB: 6 units.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query LengthMeasures --top 5
./sapb1 query LengthMeasures --count
./sapb1 query LengthMeasures --select "UnitCode,UnitName,UnitDisplay,UnitLengthinmm" --top 10
# Units of a metre or longer:
./sapb1 query LengthMeasures --filter "UnitLengthinmm ge 1000" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| UnitCode | Unit numeric key |
| UnitName | Unit full name |
| UnitDisplay | Short display symbol |
| UnitLengthinmm | Conversion factor to millimetres |
| UnitCodeforQuantityDisplay | Unit used when displaying quantities |

## Connections
- Domain: [[system-other-1]]
- [[Items]] via UnitCode — item master length/width/height dimension fields reference these units
