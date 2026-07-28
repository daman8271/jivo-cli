---
entity: IntegrationPackagesConfigure
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3
---
# IntegrationPackagesConfigure
Configuration switches for SAP B1 integration framework packages (enable/disable integration scenarios). Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query IntegrationPackagesConfigure --top 5
./sapb1 query IntegrationPackagesConfigure --count
./sapb1 query IntegrationPackagesConfigure --select "AbsEntry,Code,Name,IsEnable" --top 10
# Which integration packages are currently switched on:
./sapb1 query IntegrationPackagesConfigure --filter "IsEnable eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| Code | Package code |
| Name | Package display name |
| IsEnable | Package enabled flag |

## Connections
- Domain: [[inventory-warehouse-1]]
