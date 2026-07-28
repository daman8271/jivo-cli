---
entity: BEMReplicationPeriodService
domain: financials-accounting-1
readable: true
methods: ["BEMReplicationPeriodService_GetList"]
rows_oil: null
---
# BEMReplicationPeriodService
Lists Budget Extended Module (BEM) replication periods used to sync budget planning periods with posting periods.

## Operations
- `BEMReplicationPeriodService_GetList` (GET)
- `BEMReplicationPeriodService_GetList` (POST)

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. Entity sets are the read path in the CLI: query [[BEMReplicationPeriods]] for the same period records. Browse this service's operations with `./sapb1 ops BEMReplicationPeriodService`.

## Connections
- Domain: [[financials-accounting-1]]
- [[BEMReplicationPeriods]] — the entity set counterpart holding the replication periods (query this instead)
- Posting periods — BEM periods mirror the company's posting periods (no PostingPeriods entity set in this catalog)
