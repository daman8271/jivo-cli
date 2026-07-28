---
entity: ReportTypes
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 453
---
# ReportTypes
Catalog of every document/report type in the system with its default print layout mapping (453 types). Live rows in JIVO_OIL_HANADB: 453.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ReportTypes --top 5
./sapb1 query ReportTypes --count
./sapb1 query ReportTypes --select "TypeCode,TypeName,DefaultReportLayout,AddonName" --top 10
# Which report types cover invoices (and what layout prints by default):
./sapb1 query ReportTypes --filter "contains(TypeName,'Invoice')" --select "TypeCode,TypeName,DefaultReportLayout" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| TypeCode | Report type code (key) |
| TypeName | Report/document type name |
| DefaultReportLayout | Default print layout code |
| AddonName | Owning addon (if any) |
| AddonFormType | Addon form type id |
| MenuID | Linked B1 menu id |

## Connections
- Domain: [[administration-setup-3]]
- [[ReportLayoutsService]] via DefaultReportLayout → layout code
- [[ReportFilter]] via report type code
