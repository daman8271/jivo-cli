---
entity: MaterialRevaluation
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 100
---
# MaterialRevaluation
Inventory revaluation documents adjusting item cost/value with offsetting expense/income G/L postings. Live rows in JIVO_OIL_HANADB: 100 documents.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query MaterialRevaluation --top 5
./sapb1 query MaterialRevaluation --count
./sapb1 query MaterialRevaluation --select "DocEntry,DocNum,DocDate,RevalType,JournalMemo" --top 10
# Revaluations posted in the current fiscal year:
./sapb1 query MaterialRevaluation --filter "DocDate ge '2026-04-01'" --top 10
```
The catalog also exposes POST actions `Cancel` and `Close` on a document — out of scope under our read-only rule.

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Document internal key |
| DocNum | Document number |
| DocDate | Posting date |
| TaxDate | Tax/document date |
| RevalType | Price-change vs value-change type |
| CardCode | Related BP code (rarely used) |
| CardName | Related BP name |
| JournalMemo | Journal remark text |
| RevaluationExpenseAccount | G/L account debited on decrease |
| RevaluationIncomeAccount | G/L account credited on increase |
| TransNum | Created journal entry number |
| Series | Numbering series |
| CreationDate | Record creation date |
| MaterialRevaluationLines | Per-item revaluation rows |

## Connections
- Domain: [[system-other-1]]
- [[Items]] via MaterialRevaluationLines.ItemCode — the items being revalued
- [[ChartOfAccounts]] via RevaluationExpenseAccount / RevaluationIncomeAccount — offset G/L accounts
- [[JournalEntries]] via TransNum — the journal entry each revaluation posts
- [[BusinessPartners]] via CardCode — optional BP reference on the document
