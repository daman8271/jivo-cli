---
entity: WebClientPreferenceService
domain: administration-setup-2
readable: false
methods: ["WebClientPreferenceService_GetList"]
rows_oil: null
---
# WebClientPreferenceService
Lists per-user preference settings (locale, display options) for the SAP B1 Web Client.

## Operations
- WebClientPreferenceService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops WebClientPreferenceService
```

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] — preference settings (locale, display options) are stored per user account
