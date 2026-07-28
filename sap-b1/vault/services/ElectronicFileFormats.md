---
entity: ElectronicFileFormats
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 11
---
# ElectronicFileFormats
Registry of electronic file format definitions (EFM/bank-file and legal-reporting export formats) and where their output files land. Live rows in JIVO_OIL_HANADB: 11.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ElectronicFileFormats --top 5
./sapb1 query ElectronicFileFormats --count
./sapb1 query ElectronicFileFormats --select "FormatID,Name,OutputFilePath,Version" --top 10
# Find a format by name fragment (e.g. GST/bank formats):
./sapb1 query ElectronicFileFormats --filter "contains(Name,'GST')" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| FormatID | Format numeric key |
| Name | Format display name |
| Description | Free-text format description |
| MenuName | B1 menu entry name |
| MenuPath | B1 menu location path |
| OutputFilePath | Where exports are written |
| SchemaVersion | Format schema version |
| Version | Format definition version |

## Connections
- Domain: [[administration-setup-3]]
- No related entities recorded in recon — formats are invoked by EFM/legal-reporting runs, not joined by key.
