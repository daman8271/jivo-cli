---
entity: WeightMeasures
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 5
---
# WeightMeasures
Master list of weight units of measure (mg-based conversion factors) used on item master weight fields — 5 units defined. Live rows in JIVO_OIL_HANADB: 5.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WeightMeasures --top 5
./sapb1 query WeightMeasures --count
./sapb1 query WeightMeasures --select "UnitCode,UnitName,UnitDisplay,UnitWeightinmg" --top 10
./sapb1 query WeightMeasures --filter "UnitWeightinmg ge 1000000" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| UnitCode | Unit numeric code (key) |
| UnitName | Unit full name |
| UnitDisplay | Display abbreviation |
| UnitWeightinmg | Conversion factor to milligrams |
## Connections
- Domain: [[system-other-2]]
- [[Items]] via item master weight unit fields (Weight1Unit/Weight2Unit referencing UnitCode)
