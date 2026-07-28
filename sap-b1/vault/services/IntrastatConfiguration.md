---
entity: IntrastatConfiguration
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 30
---
# IntrastatConfiguration
EU Intrastat statistical-reporting configuration (transaction nature codes, statistical codes, supplementary units per country and date range). Live rows in JIVO_OIL_HANADB: 30.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query IntrastatConfiguration --top 5
./sapb1 query IntrastatConfiguration --count
./sapb1 query IntrastatConfiguration --select "AbsEntry,Code,Country,Descr" --top 10
# Only the codes valid for import declarations:
./sapb1 query IntrastatConfiguration --filter "Import eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Configuration record key |
| Code | Configuration code value |
| ConfID | Configuration group ID |
| ConfType | Configuration type category |
| Country | Applicable country code |
| DateFrom | Validity start date |
| DateTo | Validity end date |
| Descr | Code description text |
| Import | Valid for imports flag |
| Export | Valid for exports flag |
| StatCode | Statistical procedure code |
| SuppUnit | Supplementary unit measure |
| PrcstVal | Percentage of statistical value |
| TriangDeal | Triangular-deal indicator |

## Connections
- Domain: [[administration-setup-3]]
- [[Countries]] via Country — the EU member country each configuration row applies to
