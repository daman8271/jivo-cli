---
entity: TaxInvoiceReport
domain: sales-ar
readable: true
methods: [GET, PATCH, POST]
rows_oil: 0
---
# TaxInvoiceReport
Tax-invoice reporting documents for localization tax filings (report/cancel lifecycle); unused in JIVO_OIL. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TaxInvoiceReport --top 5
./sapb1 query TaxInvoiceReport --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields TaxInvoiceReport
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields TaxInvoiceReport` when populated.

## Connections
- Domain: [[sales-ar]]
- [[Invoices]] via reported invoice lines
- [[SalesTaxInvoices]] via reported tax-invoice lines
