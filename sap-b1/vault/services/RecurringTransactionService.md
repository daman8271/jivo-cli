---
entity: RecurringTransactionService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# RecurringTransactionService
Manages and executes recurring transaction instances generated from recurring document/posting templates.

## Operations
- RecurringTransactionService_GetAvailableRecurringTransactions
- RecurringTransactionService_DeleteRecurringTransactions
- RecurringTransactionService_GetRecurringTransaction
- RecurringTransactionService_ExecuteRecurringTransactions

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops RecurringTransactionService`. The Delete/Execute operations mutate data and are out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-2]]
- [[Orders]] via generated document instances — recurring sales orders
- [[Invoices]] via generated document instances — recurring A/R invoices
- [[JournalEntries]] via generated posting instances — recurring journal postings
