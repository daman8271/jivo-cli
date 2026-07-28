---
entity: SelfInvoices
domain: sales-ar
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# SelfInvoices
Self-billing invoices the company issues on a vendor's behalf (reverse-charge scenarios); unused in JIVO_OIL. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query SelfInvoices --top 5
./sapb1 query SelfInvoices --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields SelfInvoices
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields SelfInvoices` when populated.

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode (vendor being self-billed)
- [[Invoices]] via related A/R invoice documents
