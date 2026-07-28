---
entity: AccountsService
domain: financials-accounting-1
readable: false
methods: ["AccountsService_CreateOpenBalance"]
rows_oil: null
---
# AccountsService
Posts opening-balance journal transactions for G/L accounts during system initialization or period migration.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[ChartOfAccounts]] — the G/L accounts whose opening balances get posted (AccountCode)
- [[JournalEntries]] — opening balances land in the ledger as journal entries
