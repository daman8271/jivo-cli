---
entity: WebClientListviewFilterService
domain: administration-setup-2
readable: false
methods: ["WebClientListviewFilterService_GetList"]
rows_oil: null
---
# WebClientListviewFilterService
Lists saved list-view filters users have created in the SAP B1 Web Client.

## Operations
- WebClientListviewFilterService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientListviewFilterService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — saved list-view filters belong to the user account that created them
