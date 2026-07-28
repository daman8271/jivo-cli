---
entity: DunningLetters
domain: sales-ar
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# DunningLetters
Stores generated dunning (payment-reminder) letters sent to customers with overdue invoices; unused in JIVO_OIL. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DunningLetters --top 5
./sapb1 query DunningLetters --count
# Entity set is empty — discover the schema live if it ever fills:
./sapb1 fields DunningLetters
```

## Key fields
No sample rows in JIVO_OIL (0 rows), so recon captured no field list. Discover with `./sapb1 fields DunningLetters` when populated.

## Connections
- Domain: [[sales-ar]]
- [[BusinessPartners]] via CardCode (dunned customer)
- [[Invoices]] via letter lines (overdue invoice DocEntry)
- [[DunningTerms]] via dunning term code (level rules)
