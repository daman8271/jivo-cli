---
entity: WebClientBookmarkTileService
domain: administration-setup-2
readable: false
methods: ["WebClientBookmarkTileService_GetList"]
rows_oil: null
---
# WebClientBookmarkTileService
Lists bookmark tiles saved by users on the SAP B1 Web Client home screen.

## Operations
- WebClientBookmarkTileService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientBookmarkTileService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — each bookmark tile belongs to the user account that saved it
