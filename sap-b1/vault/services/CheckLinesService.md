---
entity: CheckLinesService
domain: banking-payments
readable: false
methods: ["CheckLinesService_GetCheckLine", "CheckLinesService_GetValidCheckLineList"]
rows_oil: null
---
# CheckLinesService
RPC helper that retrieves individual check lines and lists valid (depositable) checks received from customers.
## Operations
- `CheckLinesService_GetCheckLine`
- `CheckLinesService_GetValidCheckLineList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity sets: check lines live on [[IncomingPayments]] (Checks collection) and deposited checks on [[Deposits]]. Browse this service's operations with `./sapb1 ops CheckLinesService`.
## Connections
- Domain: [[banking-payments]]
- [[IncomingPayments]] — payments whose check rows this service reads
- [[Deposits]] — deposits that consume the valid check lines
- [[Banks]] — drawee bank on each check line
