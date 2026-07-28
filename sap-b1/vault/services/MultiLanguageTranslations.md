---
entity: MultiLanguageTranslations
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 65
---
# MultiLanguageTranslations
Stores per-field translated values of master-data records (table + field + key → translations per language) for multi-language printing. Live rows in JIVO_OIL_HANADB: 65.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query MultiLanguageTranslations --top 5
./sapb1 query MultiLanguageTranslations --count
./sapb1 query MultiLanguageTranslations --select "Numerator,TableName,FieldAlias,PrimaryKeyofobject" --top 10
# All translated item-master fields (OITM):
./sapb1 query MultiLanguageTranslations --filter "TableName eq 'OITM'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Numerator | Translation record key |
| TableName | Source master-data table |
| FieldAlias | Translated field name |
| PrimaryKeyofobject | Source record key value |
| TranslationsInUserLanguages | Per-language translated values |

## Connections
- Domain: [[administration-setup-3]]
- [[ExtendedTranslations]] — the companion extended-translation store (empty in this DB)
