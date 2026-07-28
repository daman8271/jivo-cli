---
entity: WebClientNotificationService
domain: administration-setup-2
readable: false
methods: ["WebClientNotificationService_GetList"]
rows_oil: null
---
# WebClientNotificationService
Lists in-app notifications delivered to users in the SAP B1 Web Client.

## Operations
- WebClientNotificationService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientNotificationService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — notifications are delivered to individual user accounts
