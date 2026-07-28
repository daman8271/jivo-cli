---
entity: JournalEntries
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, Cancel]
rows_oil: 131295
---
# JournalEntries
The core G/L journal — every accounting transaction (manual and document-generated) with debit/credit lines; 131k rows in JIVO_OIL. Live rows in JIVO_OIL_HANADB: 131295.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query JournalEntries --top 5
./sapb1 query JournalEntries --count
./sapb1 query JournalEntries --select "JdtNum,ReferenceDate,Memo,TransactionCode" --top 10
```
Useful filter — postings in the current India fiscal year (large set: always filter + `--orderby`):
```bash
./sapb1 query JournalEntries --filter "ReferenceDate ge '2026-04-01'" --orderby "ReferenceDate desc" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| JdtNum | Journal transaction number (key) |
| Number | Journal voucher series number |
| ReferenceDate | Posting date |
| DueDate | Due date |
| TaxDate | Document/tax date |
| Memo | Header remarks |
| Reference | Reference 1 (often DocNum) |
| Reference2 | Reference 2 |
| TransactionCode | Transaction code tag |
| ProjectCode | Header project code |
| DocumentType | Manual JE document type |
| Original | Originating document entry |
| LocationCode | Branch/location |
| JournalEntryLines | Debit/credit line collection |

## Connections
- Domain: [[financials-accounting-2]]
- [[ChartOfAccounts]] via JournalEntryLines.AccountCode — every line hits one G/L account
- [[Projects]] via ProjectCode (header) and line-level project codes
- [[BusinessPartners]] via JournalEntryLines.ShortName when the line posts to a BP control account
- [[ProfitCenters]] via JournalEntryLines.CostingCode (dimension allocations)
- [[JournalEntryDocumentTypes]] via DocumentType on manual entries
