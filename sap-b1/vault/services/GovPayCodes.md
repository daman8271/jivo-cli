---
entity: GovPayCodes
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# GovPayCodes
Government payment codes used in localization payment/reporting files (e.g. tax authority payment identifiers); unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query GovPayCodes --top 5
./sapb1 query GovPayCodes --count
# Table is empty here; discover fields once populated:
./sapb1 fields GovPayCodes
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Standard shape is an AbsEntry key with the government payment code and its description; confirm with `./sapb1 fields GovPayCodes` once populated.

## Connections
- Domain: [[administration-setup-3]]
- No related entities recorded in recon — localization payment-file lookup, unused here.
