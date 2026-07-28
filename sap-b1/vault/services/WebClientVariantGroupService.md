---
entity: WebClientVariantGroupService
domain: administration-setup-2
readable: false
methods: ["WebClientVariantGroupService_GetList"]
rows_oil: null
---
# WebClientVariantGroupService
Lists variant groups that bundle saved view variants in the SAP B1 Web Client.

## Operations
- WebClientVariantGroupService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientVariantGroupService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — variant groups bundle the view variants a user account has saved
