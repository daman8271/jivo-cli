---
entity: TransactionCodesService
domain: administration-setup-2
readable: false
methods: ["TransactionCodesService_GetList"]
rows_oil: null
---
# TransactionCodesService
Returns the list of journal transaction codes used to classify journal entries in financials.

## Operations
- TransactionCodesService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops TransactionCodesService
```

## Connections
- Domain: [[administration-setup-2]]
- [[JournalEntries]] — journal entries carry a TransactionCode field classified by these codes
