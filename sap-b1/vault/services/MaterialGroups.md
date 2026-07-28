---
entity: MaterialGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# MaterialGroups
Brazil localization material groups for item fiscal classification; unused in this Indian database. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query MaterialGroups --top 5
./sapb1 query MaterialGroups --count
# Table is empty here; discover fields once populated:
./sapb1 fields MaterialGroups
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Standard shape is an AbsEntry key with Code and Description; confirm with `./sapb1 fields MaterialGroups` once populated.

## Connections
- Domain: [[administration-setup-3]]
- [[Items]] — items carry a material group in their Brazil fiscal classification (unused in this Indian DB)
