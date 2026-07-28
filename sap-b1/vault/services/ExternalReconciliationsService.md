---
entity: ExternalReconciliationsService
domain: administration-setup-1
readable: false
methods: [Reconcile, GetReconciliation, CancelReconciliation, GetReconciliationList]
rows_oil: null
---
# ExternalReconciliationsService
Performs and manages external reconciliations matching G/L or BP transactions against bank/external statements.

## Operations
- Reconcile
- GetReconciliation
- CancelReconciliation
- GetReconciliationList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops ExternalReconciliationsService`. Note that Reconcile/CancelReconciliation are write actions and stay out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-1]]
- [[ChartOfAccounts]] via AcctCode — the G/L account whose transactions are reconciled
- [[BusinessPartners]] via CardCode — the BP whose transactions are reconciled
- [[JournalEntries]] via TransId — the journal transactions matched in a reconciliation
