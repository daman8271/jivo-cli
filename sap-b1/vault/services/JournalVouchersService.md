---
entity: JournalVouchersService
domain: financials-accounting-1
readable: false
methods: ["JournalVouchersService_Add"]
rows_oil: null
---
# JournalVouchersService
Creates draft journal vouchers (unposted journal entry batches) awaiting review before posting to the general ledger.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[JournalEntries]] — vouchers become journal entries once reviewed and posted
- [[ChartOfAccounts]] — voucher lines debit/credit G/L accounts (AccountCode)
- [[Projects]] — voucher lines can be tagged to a project (ProjectCode)
