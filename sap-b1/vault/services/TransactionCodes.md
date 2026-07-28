---
entity: TransactionCodes
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# TransactionCodes
Journal-entry transaction code master for tagging/classifying G/L postings; unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TransactionCodes --top 5
./sapb1 query TransactionCodes --count
./sapb1 query TransactionCodes --select "Code,Description" --top 10
# Look up one transaction code (if ever populated):
./sapb1 query TransactionCodes --filter "Code eq 'ADJ'" --top 5
```
Set is empty here — confirm live field names with `./sapb1 fields TransactionCodes` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| Code | Transaction code (key) |
| Description | Code meaning/label |

(No key fields captured in recon — the set is empty; fields above are the standard Service Layer schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[JournalEntries]] via TransactionCode on the journal header
