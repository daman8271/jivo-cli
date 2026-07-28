---
entity: CorrectionInvoiceReversal
domain: sales-ar
readable: true
methods: ["GET CorrectionInvoiceReversal(id)", "GET CorrectionInvoiceReversal", "POST CorrectionInvoiceReversal", "PATCH CorrectionInvoiceReversal(id)", "POST CorrectionInvoiceReversal(id)/Close", "POST CorrectionInvoiceReversal(id)/Cancel", "POST CorrectionInvoiceReversal(id)/Reopen", "POST CorrectionInvoiceReversal(id)/CreateCancellationDocument"]
rows_oil: 0
---
# CorrectionInvoiceReversal
Reversal documents that undo posted A/R correction invoices; unused in JIVO_OIL_HANADB so key fields come from the standard marketing-document schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CorrectionInvoiceReversal --top 5
./sapb1 query CorrectionInvoiceReversal --count
./sapb1 query CorrectionInvoiceReversal --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Non-cancelled reversals only (expect none in this DB):
./sapb1 query CorrectionInvoiceReversal --filter "Cancelled eq 'tNO'" --select "DocNum,CardName,DocDate,DocTotal"
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
| DocTotal | Total document value |
| DocCurrency | Document currency |
| DocumentStatus | Open or closed |
| SalesPersonCode | Sales employee code |
| Comments | Free-text remarks |
| NumAtCard | Customer reference number |
| Cancelled | Cancellation flag |
| TaxDate | Tax/VAT posting date |
## Connections
- Domain: [[sales-ar]]
- [[CorrectionInvoice]] via DocumentLines BaseEntry/BaseType — the correction invoice being reversed
- [[BusinessPartners]] via CardCode — the customer on the reversed correction
- [[Items]] via DocumentLines/ItemCode — reversed item lines
- [[SalesPersons]] via SalesPersonCode — sales employee on the document
