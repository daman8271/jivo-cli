---
entity: WebClientLaunchpadService
domain: administration-setup-2
readable: false
methods: ["WebClientLaunchpadService_GetList"]
rows_oil: null
---
# WebClientLaunchpadService
Lists launchpad (home page tile group) configurations in the SAP B1 Web Client.

## Operations
- WebClientLaunchpadService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientLaunchpadService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — launchpad tile-group configurations belong to individual user accounts
