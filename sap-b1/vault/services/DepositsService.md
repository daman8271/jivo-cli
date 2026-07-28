---
entity: DepositsService
domain: banking-payments
readable: false
methods: ["DepositsService_GetDepositList", "DepositsService_CancelCheckRow", "DepositsService_CancelCheckRowbyCurrentSystemDate"]
rows_oil: null
---
# DepositsService
RPC service for the deposits workflow: listing deposits and cancelling individual check rows within them.
## Operations
- `DepositsService_GetDepositList`
- `DepositsService_CancelCheckRow` — WRITE, out of scope under the standing READ-ONLY rule
- `DepositsService_CancelCheckRowbyCurrentSystemDate` — WRITE, out of scope under the standing READ-ONLY rule

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[Deposits]] directly. Browse this service's operations with `./sapb1 ops DepositsService`.
## Connections
- Domain: [[banking-payments]]
- [[Deposits]] — the entity set holding deposit documents (query this instead)
- [[IncomingPayments]] — source payments whose checks get deposited
- [[Banks]] — bank the deposit is made into
