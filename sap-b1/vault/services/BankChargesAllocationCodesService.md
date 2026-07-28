---
entity: BankChargesAllocationCodesService
domain: banking-payments
readable: false
methods: ["BankChargesAllocationCodesService_GetBankChargesAllocationCodeList"]
rows_oil: null
---
# BankChargesAllocationCodesService
RPC helper that returns the list of bank-charge allocation codes used to book bank fees on payments.
## Operations
- `BankChargesAllocationCodesService_GetBankChargesAllocationCodeList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[BankChargesAllocationCodes]] directly. Browse this service's operations with `./sapb1 ops BankChargesAllocationCodesService`.
## Connections
- Domain: [[banking-payments]]
- [[BankChargesAllocationCodes]] — the entity set holding the same allocation codes (query this instead)
