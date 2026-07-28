---
entity: AccrualTypes
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# AccrualTypes
Defines accrual type codes used to classify expense/revenue accruals in period-end accounting; empty in JIVO_OIL_HANADB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AccrualTypes --top 5
./sapb1 query AccrualTypes --count
./sapb1 query AccrualTypes --select "Code,Name" --top 10
# If ever populated, look up an accrual type by name fragment:
./sapb1 query AccrualTypes --filter "contains(Name,'Accrual')" --top 5
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Standard fields are Code (numeric key) and Name (type label); confirm with `./sapb1 fields AccrualTypes` once populated.

## Connections
- Domain: [[administration-setup-3]]
- No related entities recorded in recon — standalone accounting lookup, unused here.
