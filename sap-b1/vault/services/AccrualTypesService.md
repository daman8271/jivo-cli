---
entity: AccrualTypesService
domain: administration-setup-1
readable: true
methods: [AccrualTypesService_GetAccrualTypeList]
rows_oil: null
---
# AccrualTypesService
Lists accrual types used for period-end expense/revenue accrual postings in financial accounting.

## Operations
- `AccrualTypesService_GetAccrualTypeList` (GET)
- `AccrualTypesService_GetAccrualTypeList` (POST)

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. Entity sets are the read path in the CLI: query [[AccrualTypes]] for the same accrual type records. Browse this service's operations with `./sapb1 ops AccrualTypesService`.

## Connections
- Domain: [[administration-setup-1]]
- [[AccrualTypes]] — the entity set counterpart holding the accrual type records (query this instead)
