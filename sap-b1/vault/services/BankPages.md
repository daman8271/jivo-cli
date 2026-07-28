---
entity: BankPages
domain: banking-payments
readable: true
methods: ["GET BankPages", "GET BankPages(id)", "POST BankPages", "PATCH BankPages(id)", "DELETE BankPages(id)"]
rows_oil: 0
---
# BankPages
Imported external bank-statement rows (the 'bank pages' used in external reconciliation) matching bank movements to G/L accounts and business partners. Empty in JIVO_OIL_HANADB. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BankPages --top 5
./sapb1 query BankPages --count
./sapb1 query BankPages --select "Sequence,CardCode,DueDate,DebitAmount,CreditAmount" --top 10
# Statement rows not yet turned into payments:
./sapb1 query BankPages --filter "PaymentCreated eq 'tNO'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| Sequence | Row internal sequence key |
| AccountCode | Matched G/L account |
| AccountName | G/L account name |
| CardCode | Matched business partner |
| CardName | Business partner name |
| StatementNumber | Source statement number |
| Reference | Bank reference text |
| DueDate | Value date of movement |
| DebitAmount | Debit (outflow) amount |
| CreditAmount | Credit (inflow) amount |
| Memo | Free-text memo |
| PaymentReference | Payment reference number |
| InvoiceNumber | Matched invoice number |
| PaymentCreated | Payment generated flag |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via CardCode — partner matched to the bank movement
- [[ChartOfAccounts]] via AccountCode — G/L account matched to the movement
- [[BankStatements]] via StatementNumber — statement the row was imported from
