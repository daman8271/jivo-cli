---
entity: WebClientDashboardService
domain: administration-setup-2
readable: false
methods: ["WebClientDashboardService_GetList"]
rows_oil: null
---
# WebClientDashboardService
Lists analytical dashboards configured in the SAP B1 Web Client.

## Operations
- WebClientDashboardService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientDashboardService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — dashboards are configured per user account in the Web Client
