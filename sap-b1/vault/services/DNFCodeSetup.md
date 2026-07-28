---
entity: DNFCodeSetup
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# DNFCodeSetup
Brazil localization DNF (fiscal declaration) code setup for items; unused in this Indian database. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DNFCodeSetup --top 5
./sapb1 query DNFCodeSetup --count
# Table is empty here; discover fields once populated:
./sapb1 fields DNFCodeSetup
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Standard shape is an AbsEntry key with Code and Description; confirm with `./sapb1 fields DNFCodeSetup` once populated.

## Connections
- Domain: [[administration-setup-3]]
- [[Items]] — items carry a DNF code in their Brazil fiscal classification (unused in this Indian DB)
