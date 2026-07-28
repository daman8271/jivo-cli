---
entity: WebClientFormSettingService
domain: administration-setup-2
readable: false
methods: ["WebClientFormSettingService_GetList"]
rows_oil: null
---
# WebClientFormSettingService
Lists per-user form/field layout settings for SAP B1 Web Client screens.

## Operations
- WebClientFormSettingService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientFormSettingService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — form and field layout settings are stored per user account
