---
entity: WebClientVariantService
domain: administration-setup-2
readable: false
methods: ["WebClientVariantService_GetList"]
rows_oil: null
---
# WebClientVariantService
Lists saved view variants (personalized screen states) in the SAP B1 Web Client.

## Operations
- WebClientVariantService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientVariantService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — each saved view variant is a personalized screen state owned by a user account
