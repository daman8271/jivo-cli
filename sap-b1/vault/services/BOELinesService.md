---
entity: BOELinesService
domain: banking-payments
readable: false
methods: ["BOELinesService_GetBOELine"]
rows_oil: null
---
# BOELinesService
RPC helper that fetches an individual bill-of-exchange line for BOE management.
## Operations
- `BOELinesService_GetBOELine`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[BillOfExchangeTransactions]] directly. Browse this service's operations with `./sapb1 ops BOELinesService`.
## Connections
- Domain: [[banking-payments]]
- [[BillOfExchangeTransactions]] — the entity set the BOE lines belong to (query this instead)
