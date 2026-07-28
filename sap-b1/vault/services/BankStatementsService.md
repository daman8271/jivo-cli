---
entity: BankStatementsService
domain: banking-payments
readable: false
methods: ["BankStatementsService_GetBankStatementList"]
rows_oil: null
---
# BankStatementsService
RPC helper that lists imported bank statements for the bank-statement processing (BSP) workflow.
## Operations
- `BankStatementsService_GetBankStatementList`

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity set: query [[BankStatements]] directly. Browse this service's operations with `./sapb1 ops BankStatementsService`.
## Connections
- Domain: [[banking-payments]]
- [[BankStatements]] — the entity set holding the imported statements (query this instead)
