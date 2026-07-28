---
entity: CorrectionInvoice
domain: sales-ar
readable: true
methods: ["GET CorrectionInvoice(id)", "GET CorrectionInvoice", "POST CorrectionInvoice", "PATCH CorrectionInvoice(id)", "POST CorrectionInvoice(id)/Close", "POST CorrectionInvoice(id)/Cancel", "POST CorrectionInvoice(id)/Reopen", "POST CorrectionInvoice(id)/CreateCancellationDocument"]
rows_oil: 0
---
# CorrectionInvoice
A/R correction invoices (localization feature to correct posted invoices without credit notes); unused in JIVO_OIL_HANADB so key fields come from the standard marketing-document schema. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CorrectionInvoice --top 5
./sapb1 query CorrectionInvoice --count
./sapb1 query CorrectionInvoice --select "DocNum,CardName,DocDate,DocTotal" --top 10
# Still-open correction invoices (expect none in this DB):
./sapb1 query CorrectionInvoice --filter "DocumentStatus eq 'bost_Open'" --select "DocNum,CardName,DocDate,DocTotal"
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
- [[BusinessPartners]] via CardCode — the customer whose invoice is corrected
- [[Items]] via DocumentLines/ItemCode — corrected item lines
- [[Invoices]] via DocumentLines BaseEntry/BaseType — the posted invoice being corrected
- [[SalesPersons]] via SalesPersonCode — sales employee on the document
- [[Currencies]] via DocCurrency — currency of DocTotal
