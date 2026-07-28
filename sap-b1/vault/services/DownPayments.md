---
entity: DownPayments
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# DownPayments
A/R down-payment invoices billing customers in advance, later applied against final invoices. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DownPayments --top 5
./sapb1 query DownPayments --count
./sapb1 query DownPayments --select "DocNum,CardCode,DocDate,DocTotal" --top 10
# still-open down payments not yet applied to a final invoice
./sapb1 query DownPayments --filter "DocumentStatus eq 'bost_Open'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal key |
| DocNum | Document number |
| CardCode | Customer BP code |
| CardName | Customer name |
| DocDate | Posting date |
| DocDueDate | Due date |
| DocTotal | Document total |
| VatSum | Tax amount |
| DocCurrency | Document currency |
| DownPaymentType | Invoice / request type |
| SalesPersonCode | Sales employee |
| Comments | Free-text remarks |
| DocumentStatus | Open / closed |
| PayToCode | Pay-to address ID |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via CardCode — the customer billed in advance
- [[Orders]] — base sales order the advance is drawn against
- [[Invoices]] — final A/R invoice the down payment is applied to
- [[IncomingPayments]] — receipt that pays the down-payment invoice
- [[SalesPersons]] via SalesPersonCode — owning sales employee
- [[Currencies]] via DocCurrency — document currency
