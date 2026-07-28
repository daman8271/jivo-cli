---
entity: BPOpeningBalanceService
domain: administration-setup-1
readable: false
methods: [BPOpeningBalanceService_CreateOpenBalance]
rows_oil: null
---
# BPOpeningBalanceService
Creates opening balance journal postings for business partners during system initialization (write-only; off-limits in this read-only setup).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[BusinessPartners]] — the partner whose opening balance gets posted (CardCode)
- [[JournalEntries]] — opening balances land in the ledger as journal entries
