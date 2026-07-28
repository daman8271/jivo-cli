---
entity: PurchaseDownPayments
domain: banking-payments
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# PurchaseDownPayments
A/P down-payment invoices for advances paid to vendors, later netted against final purchase invoices. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query PurchaseDownPayments --top 5
./sapb1 query PurchaseDownPayments --count
./sapb1 query PurchaseDownPayments --select "DocNum,CardCode,DocDate,DocTotal" --top 10
# open advances not yet netted against a final purchase invoice
./sapb1 query PurchaseDownPayments --filter "DocumentStatus eq 'bost_Open'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal key |
| DocNum | Document number |
| CardCode | Vendor BP code |
| CardName | Vendor name |
| DocDate | Posting date |
| DocDueDate | Due date |
| DocTotal | Document total |
| VatSum | Tax amount |
| DocCurrency | Document currency |
| DownPaymentType | Invoice / request type |
| Comments | Free-text remarks |
| DocumentStatus | Open / closed |
| PayToCode | Pay-to address ID |
| Project | Project code |
## Connections
- Domain: [[banking-payments]]
- [[BusinessPartners]] via CardCode — the vendor paid in advance
- [[PurchaseOrders]] — base purchase order the advance is drawn against
- [[PurchaseInvoices]] — final A/P invoice the advance is netted against
- [[VendorPayments]] — outgoing payment that settles the advance
- [[Projects]] via Project — project dimension
- [[Currencies]] via DocCurrency — document currency
