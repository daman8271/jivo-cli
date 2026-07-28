---
entity: KPIs
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 6
---
# KPIs
Definitions of key-performance-indicator widgets shown on B1 cockpit/Fiori dashboards. Live rows in JIVO_OIL_HANADB: 6 defined.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query KPIs --top 5
./sapb1 query KPIs --count
./sapb1 query KPIs --select "KPICode,KPIName,KPIType,NumberOfColumns" --top 10
# Multi-column KPI widgets only:
./sapb1 query KPIs --filter "NumberOfColumns gt 1" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| KPICode | KPI numeric key |
| KPIName | KPI display name |
| KPIType | Widget/measure type |
| NumberOfColumns | Columns in the widget layout |
| KPI_ItemLines | Measure/line definitions collection |

## Connections
- Domain: [[system-other-1]]
