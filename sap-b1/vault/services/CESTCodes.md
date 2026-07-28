---
entity: CESTCodes
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CESTCodes
Brazil localization CEST tax substitution codes assigned to items; not used in this Indian database. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CESTCodes --top 5
./sapb1 query CESTCodes --count
# Table is empty here; discover fields once populated:
./sapb1 fields CESTCodes
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Standard shape is an AbsEntry key with Code and Description; confirm with `./sapb1 fields CESTCodes` once populated.

## Connections
- Domain: [[administration-setup-3]]
- [[Items]] — items carry a CEST code in their Brazil fiscal tax info (unused in this Indian DB)
