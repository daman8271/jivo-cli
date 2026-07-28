---
entity: ExtendedTranslations
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ExtendedTranslations
Extended multi-language translations of master-data field values for foreign-language documents; unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ExtendedTranslations --top 5
./sapb1 query ExtendedTranslations --count
# Table is empty here; discover fields once populated:
./sapb1 fields ExtendedTranslations
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Expect a translation key plus source table/field/record references and per-language values; confirm with `./sapb1 fields ExtendedTranslations` once populated.

## Connections
- Domain: [[administration-setup-3]]
- [[MultiLanguageTranslations]] — the companion (and here, actually-populated) translation store for master-data fields
