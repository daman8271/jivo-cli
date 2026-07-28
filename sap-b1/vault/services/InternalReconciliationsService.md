---
entity: InternalReconciliationsService
domain: administration-setup-1
readable: false
methods: [GetOpenTransactions, Cancel, RequestApproveCancellation]
rows_oil: null
---
# InternalReconciliationsService
Manages internal reconciliation of open BP/G/L transactions (e.g. matching invoices to payments) including cancellation workflows.

## Operations
- GetOpenTransactions
- Cancel
- RequestApproveCancellation

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops InternalReconciliationsService`. Note that Cancel/RequestApproveCancellation are write actions and stay out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-1]]
- [[ChartOfAccounts]] via AcctCode — G/L accounts whose open transactions are matched
- [[BusinessPartners]] via CardCode — BPs whose open invoices/payments are matched
- [[JournalEntries]] via TransId — the journal transactions being reconciled
