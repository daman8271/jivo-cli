---
entity: SalesTaxInvoices
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# SalesTaxInvoices
Localization-specific sales tax invoices issued separately from A/R invoices for tax reporting; unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SalesTaxInvoices --top 5
./sapb1 query SalesTaxInvoices --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields SalesTaxInvoices
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields SalesTaxInvoices` when populated.

## Connections
- Domain: [[sales-ar]]
- [[Invoices]] via base A/R invoice reference
- [[BusinessPartners]] via CardCode
