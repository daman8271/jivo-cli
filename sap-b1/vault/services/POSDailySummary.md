---
entity: POSDailySummary
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# POSDailySummary
Aggregated point-of-sale daily sales summary documents for consolidated POS posting. Live rows in JIVO_OIL_HANADB: 0 — no POS integration posts here.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query POSDailySummary --top 5
./sapb1 query POSDailySummary --count
./sapb1 query POSDailySummary --select "DocEntry,DocNum,DocDate,PostingDate" --top 10
# Summaries posted this calendar year (if POS ever goes live):
./sapb1 query POSDailySummary --filter "DocDate ge '2026-01-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Document internal key |
| DocNum | Document number |
| DocDate | Summary business date |
| PostingDate | G/L posting date |

## Connections
- Domain: [[system-other-1]]
- [[Invoices]] via consolidated POS postings — daily summary rolls POS sales into A/R invoices
- [[IncomingPayments]] via consolidated POS postings — matching daily payment totals
