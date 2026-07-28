---
entity: CreditNotes
domain: sales-ar
readable: true
methods: ["GET CreditNotes(id)", "GET CreditNotes", "POST CreditNotes", "PATCH CreditNotes(id)", "DELETE CreditNotes(id)", "POST CreditNotes(id)/Close", "POST CreditNotes(id)/Cancel", "POST CreditNotes(id)/Reopen", "POST CreditNotes(id)/CreateCancellationDocument"]
rows_oil: 6351
---
# CreditNotes
A/R credit memos issued to customers to reverse invoiced value or returned goods. Live rows in JIVO_OIL_HANADB: 6,351.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CreditNotes --top 5
./sapb1 query CreditNotes --count
./sapb1 query CreditNotes --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Credit memos posted this fiscal year (since 1 Apr 2026):
./sapb1 query CreditNotes --filter "DocDate ge '2026-04-01'" --select "DocNum,CardName,DocDate,DocTotal" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Visible document number |
| CardCode | Customer code |
| CardName | Customer name |
| DocDate | Posting date |
| DocDueDate | Due/value date |
| DocTotal | Total credited value |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| SalesPersonCode | Sales employee code |
| NumAtCard | Customer reference number |
| Comments | Free-text remarks |
| Cancelled | Cancellation flag |
| BPL_IDAssignedToInvoice | Branch (business place) ID |
## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode — the customer receiving the credit
- [[Items]] via DocumentLines/ItemCode — what was credited, line by line
- [[Invoices]] via DocumentLines BaseEntry/BaseType — the invoice the memo credits
- [[Returns]] via document chain (Base/Target refs) — goods returns drawn into credit memos
- [[SalesPersons]] via SalesPersonCode — sales employee on the document
- [[Warehouses]] via DocumentLines/WarehouseCode — stock re-enters this warehouse on credit with goods
- [[Currencies]] via DocCurrency — currency of DocTotal
- [[Projects]] via DocumentLines/ProjectCode — project assignment per line
