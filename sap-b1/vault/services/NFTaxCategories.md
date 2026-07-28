---
entity: NFTaxCategories
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 9
---
# NFTaxCategories
Nota Fiscal tax categories (Brazil localization) grouping tax codes for fiscal document processing. Live rows in JIVO_OIL_HANADB: 9.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query NFTaxCategories --top 5
./sapb1 query NFTaxCategories --count
./sapb1 query NFTaxCategories --select "AbsId,Code,GPCId,Locked" --top 10
```
Useful filter — only the unlocked (editable) categories:
```bash
./sapb1 query NFTaxCategories --filter "Locked eq 'tNO'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsId | Internal ID (key) |
| Code | Tax category code |
| GPCId | Global posting category ID |
| CESTrel | CEST relevance flag |
| Locked | System-locked flag |

## Connections
- Domain: [[financials-accounting-2]]
- [[VatGroups]] via tax codes grouped under each category
